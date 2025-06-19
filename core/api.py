import os
import re
import math
import json
import cv2
import markdown
import traceback
import boto3
import time
import threading
import botocore.exceptions
from bs4 import BeautifulSoup
from PIL import Image

from core.vectorizers import SentBERTVectorizer
from core.vectorizers import CPCVectorizer
from core.index_selection import SubclassBasedIndexSelector
from core.filters import FilterArray, KeywordFilter, CountryCodeFilter
from core.filters import FilingDateFilter, PublicationDateFilter, PriorityDateFilter
from core.obvious import Combiner
from core.indexes import IndexesDirectory
from core.documents import Document, Patent
from core.snippet import SnippetExtractor
from core.reranking import ConceptMatchRanker
from core.encoders import default_boe_encoder
from core.results import SearchResult
from core.encoders import default_embedding_matrix
from core.datasets import PoC
import core.remote as remote
import core.utils as utils
from services import vector_search as vector_search_srv

from config.config import (
    indexes_dir,
    reranker_active,
    smart_index_selection_active,
    year_wise_indexes,
    allow_outgoing_extension_requests,
    allow_incoming_extension_requests,
    docs_dir
)

if not vector_search_srv.ready():
    thread = threading.Thread(target=vector_search_srv.start)
    thread.start()
    while not vector_search_srv.ready():
        print("Waiting for vector search service to be ready...")
        time.sleep(1)

vectorize_text = SentBERTVectorizer().embed
available_indexes = IndexesDirectory(indexes_dir)
select_indexes = SubclassBasedIndexSelector(available_indexes).select
extract_snippet = SnippetExtractor.extract_snippet
generate_mapping = SnippetExtractor.map
reranker = None if not reranker_active else ConceptMatchRanker()

PQAI_S3_BUCKET_NAME = os.environ['PQAI_S3_BUCKET_NAME']
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)
s3 = session.resource('s3')

class APIRequest():
    
    def __init__(self, req_data=None):
        self._data = req_data
        self._validate()

    def serve(self):
        try:
            response = self._serving_fn()
            return self._formatting_fn(response)
        except BadRequestError as e:
            raise e
        except ResourceNotFoundError as e:
            raise e
        except Exception:
            traceback.print_exc()
            raise ServerError()

    def _validate(self):
        self._validation_fn()

    def _serving_fn(self):
        pass

    def _validation_fn(self):
        pass

    def _formatting_fn(self, response):
        return response


class BadRequestError(Exception):

    def __init__(self, msg='Invalid request.'):
        self.message = msg


class ServerError(Exception):

    def __init__(self, msg='Server error while handling request.'):
        self.message = msg


class NotAllowedError(Exception):

    def __init__(self, msg="Request disallowed."):
        self.message = msg


class ResourceNotFoundError(Exception):

    def __init__(self, msg="Resource not found."):
        self.message = msg


class SearchRequest(APIRequest):

    _name = 'Search Request'

    def __init__(self, req_data):
        super().__init__(req_data)
        self._query = req_data.get('q', '')
        self._latent_query = req_data.get('lq', '')

        self._offset = max(0, int(req_data.get('offset', 0)))
        self._n_results = int(req_data.get('n', 10))
        self._n_results += self._offset # for pagination

        self._doctype = req_data.get('type', 'patent')
        self._doctype = self._doctype if self._doctype in ['patent', 'npl', 'any'] else None

        self._filters = FilterExtractor(self._data).extract()
        self._indexes = self._get_indexes()

        self._need_snippets = self._read_bool_value('snip')
        self._need_mappings = self._read_bool_value('maps')
        self.MAX_RES_LIMIT = 500
        self.MIN_SIMILARITY_THRESHOLD = 0.5

    def __repr__(self):
        return f'{self._name}: {json.dumps(self._data)}'

    def __str__(self):
        return f'[{self._name}]'

    def _serving_fn(self):
        return self._searching_fn()

    def _searching_fn(self):
        pass

    def _get_indexes(self):
        if self._index_specified_in_request():
            index_in_req = self._data['idx']
            return index_in_req

        if smart_index_selection_active:
            return select_indexes(self._query, 3)

        index_ids = list(available_indexes.available())

        if "type" in self._data and (self._data['type'] not in ['any', 'auto']):
            index_ids = [idx for idx in index_ids if len(idx.split(".")) > 1
                                                     and idx.split(".")[1] == self._data['type']]

        if not year_wise_indexes:
            return index_ids

        if not self._data.get('before') and not self._data.get('after'):
            return index_ids

        if "before" in self._data and re.match(r"\d{4}", self._data['before']):
            year = int(self._data['before'][:4])
            index_ids = [idx for idx in index_ids if int(idx.split(".")[0]) <= year]

        if "after" in self._data and re.match(r"^\d{4}", self._data['after']):
            year = int(self._data['after'][:4])
            index_ids = [idx for idx in index_ids if int(idx.split(".")[0]) >= year]

        return index_ids

    def _index_specified_in_request(self):
        req_data = self._data
        if 'idx' not in req_data:
            return False
        if req_data['idx'] == 'auto':
            return False
        return True

    def _read_bool_value(self, key):
        val = self._data.get(key)
        if ((isinstance(val, str) and val in ['true', '1', 'yes']) or
            (isinstance(val, int) and val != 0)):
            return True
        return False

    def _validation_fn(self):
        if 'q' not in self._data:
            raise BadRequestError(
                'Request does not contain a query.')

    def _add_snippet_if_needed(self, result):
        if self._need_snippets:
            result.snippet = SnippetExtractor.extract_snippet(self._query, result.full_text)

    def _add_drawing_link(self, result):
        if result.type == 'patent':
            result.image = f'https://api.projectpq.ai/patents/{result.id}/thumbnails/1'


class FilterExtractor():

    def __init__(self, req_data):
        self._data = req_data

    def extract(self):
        filters = FilterArray()
        date_filter = self._get_date_filter()
        keyword_filters = self._get_keyword_filters()
        country_code_filter = self._get_country_code_filter()
        if date_filter:
            filters.add(date_filter)
        if keyword_filters:
            for fltr in keyword_filters:
                filters.add(fltr)
        if country_code_filter:
            filters.add(country_code_filter)
        return filters

    def _get_date_filter(self):
        after = self._data.get('after', None)
        before = self._data.get('before', None)
        dtype = self._data.get('dtype', 'publication')
        if after or before:
            after = None if not bool(after) else after
            before = None if not bool(before) else before
            if dtype == 'filing':
                return FilingDateFilter(after, before)
            elif dtype == 'publication':
                return PublicationDateFilter(after, before)
            elif dtype == 'priority':
                return PriorityDateFilter(after, before)
            else:
                raise BadRequestError('Invalid date filter type.')

    def _get_keyword_filters(self):
        query = self._data.get('q', '')
        keywords = re.findall(r'\`(\-?[\w\*\?]+)\`', query)
        if not keywords:
            return None
        filters = []
        for keyword in keywords:
            if keyword.startswith('-'):
                filters.append(KeywordFilter(keyword[1:], exclude=True))
            else:
                filters.append(KeywordFilter(keyword))
        return filters
    
    def _get_country_code_filter(self):
        cc = self._data.get('cc', None)
        if cc is None:
            return

        codes = re.findall(r'\b[A-Z]{2}\b', cc.upper())
        if codes:
            return CountryCodeFilter(codes)


class SearchRequest102(SearchRequest):

    _name = '102 Search Request'

    def __init__(self, req_data):
        super().__init__(req_data)

    def _searching_fn(self):
        results = self._get_results()
        if self._n_results < 100:
            results = self._rerank(results)
        results = self._deduplicate(results)
        results = results[:self._n_results]
        return results[self._offset:]

    def _get_results(self):
        query_ = re.sub(r'\`(\-[\w\*\?]+)\`', '', self._query)
        query_ = re.sub(r"\`", "", query_)
        qvec = vectorize_text("[query] " + query_)

        results = []
        n = min(self._n_results, self.MAX_RES_LIMIT)
        m = max(25, n)
        while len(results) < n and m <= 2*self.MAX_RES_LIMIT:
            payload = {
                "vector": qvec.tolist(),
                "n_results": m,
                "type": self._doctype
            }

            # Run a vector search
            results = vector_search_srv.send(payload)
            results = [t for t in results if t[2] > self.MIN_SIMILARITY_THRESHOLD]
            results = self._deduplicate_by_score(results)
            results = self._filters.apply(results, m)

            if not results:
                break
            
            # Avoid looking for more results if the last one is a poor match
            if results[-1][2] <= self.MIN_SIMILARITY_THRESHOLD + 0.01:
                break

            m *= 2 
        return [SearchResult(*t) for t in results][:n]

    def _rerank(self, results):
        if not reranker:
            return results
        result_texts = [r.abstract for r in results]
        ranks = reranker.rank(self._query, result_texts)
        return [results[i] for i in ranks]

    def _deduplicate_by_score(self, triplets):
        if not triplets:
            return triplets

        epsilon = 0.000001
        first, subsequent = triplets[0], triplets[1:]
        output = [first]
        for this in subsequent:
            last = output[-1]
            if this[2] - last[2] >= epsilon:
                output.append(this)
                continue
            
            # when scores are too close (likely family members), prefer an English-language member
            cc_this = this[0][:2]
            cc_last = last[0][:2]
            cc_pref = ['US', 'EP', 'GB', 'CA', 'AU', 'WO', 'SG', 'IN'] # native English abstracts
            cc_rank = {cc: i for i, cc in enumerate(cc_pref)}
            default_rank = len(cc_pref)
            if cc_this != cc_last:
                rank_this = cc_rank.get(cc_this, default_rank)
                rank_last = cc_rank.get(cc_last, default_rank)
                if rank_this < rank_last:
                    output[-1] = this
                    continue
                elif rank_this > rank_last:
                    continue
        # If all triplets have nearly identical scores and none are in cc_pref,
        # only the first triplet will be returned.
        return output

    def _deduplicate(self, results):
        deduplicated = []
        titles = set()
        for result in results:
            if result.title is None: # defects in the database
                continue
            if result.title.lower() in titles:
                continue
            deduplicated.append(result)
            titles.add(result.title.lower())
        return deduplicated

    def _add_remote_results_to(self, local_results):
        if not allow_outgoing_extension_requests:
            return local_results
        remote_results = remote.search_extensions(self._data)
        return remote.merge([local_results, remote_results])

    def _formatting_fn(self, results):
        for result in results:
            self._add_snippet_if_needed(result)
            self._add_mapping_if_needed(result)
            self._add_drawing_link(result)
        results = [res.json() for res in results]
        results = self._add_remote_results_to(results)
        return {
            'results': results,
            'query': self._query,
            'latent_query': self._latent_query }

    def _add_mapping_if_needed(self, result):
        if self._need_mappings:
            try:
                result.mapping = generate_mapping(self._query, result.full_text)
            except Exception:
                traceback.print_exc()
                result.mapping = None


class SearchRequest103(SearchRequest):

    _name = '103 Search Request'

    def __init__(self, req_data):
        super().__init__(req_data)
        self._results102 = None

    def _searching_fn(self):
        docs = self._get_docs_to_combine()
        self._results102 = docs
        abstracts = [doc.abstract for doc in docs]
        combiner = Combiner(self._query, abstracts)
        n = max(50, self._n_results) # see SearchRequest102 for why max used
        index_pairs = combiner.get_combinations(n)
        combinations = [(docs[i], docs[j]) for i, j in index_pairs]
        combinations = combinations[:self._n_results]
        return combinations[self._offset:]

    def _get_docs_to_combine(self):
        params = self._get_interim_request_params()
        interim_req = SearchRequest102(params)
        results = interim_req.serve()['results']
        return [SearchResult(r['id'], r['index'], r['score']) for r in results]

    def _get_interim_request_params(self):
        params = self._data.copy()
        params['n'] = 100
        params['maps'] = 0
        params['snip'] = 0
        params['offset'] = 0
        return params

    def _formatting_fn(self, combinations):
        for combination in combinations:
            for result in combination:
                self._add_snippet_if_needed(result)
                self._add_drawing_link(result)
            self._add_mapping_if_needed(combination)
        return {
            'results': [[r.json() for r in c] for c in combinations],
            'query': self._query,
            'latent_query': self._latent_query }

    def _add_mapping_if_needed(self, combination):
        if not self._need_mappings:
            return
        for result in combination:
            try:
                result.mapping = generate_mapping(self._query, result.full_text)
            except:  # noqa: E722
                result.mapping = None


class SearchRequestCombined102and103(SearchRequest103):

    _name = 'Combined Search Request'

    def __init__(self, req_data):
        super().__init__(req_data)

    def _searching_fn(self):
        results103 = super()._searching_fn()
        results102 = self._results102[:self._n_results][self._offset:]
        results = self._merge_102_and_103_results(results102, results103)
        return results[:self._n_results][self._offset:]

    def _merge_102_and_103_results(self, results102, results103):
        results = []
        p1 = 0
        p2 = 0
        while (p1 < len(results102) and p2 < len(results103)):
            r1 = results102[p1]
            r2 = results103[p2]
            if (r1.score <= min(r2[0].score, r2[1].score)):
                results.append(r1)
                p1 += 1
            else:
                results.append(r2)
                p2 += 1
        results += results102[p1:] + results103[p2:]
        return results

    def _formatting_fn(self, results):
        arr = []
        for result in results:
            if isinstance(result, SearchResult):
                self._add_snippet_if_needed(result)
                self._add_mapping_if_needed(result)
                self._add_drawing_link(result)
                arr.append(result.json())
            else:
                for r in result:
                    self._add_snippet_if_needed(r)
                    self._add_drawing_link(r)
                    self._add_mapping_if_needed(result)
                arr.append([r.json() for r in result])
        return {
            'results': arr,
            'query': self._query,
            'latent_query': self._latent_query }

    def _add_mapping_if_needed(self, result):
        if self._need_mappings:
            try:
                result.mapping = generate_mapping(self._query, result.full_text)
            except:  # noqa: E722
                result.mapping = None


class SimilarPatentsRequest(APIRequest):

    def __init__(self, req_data):
        super().__init__(req_data)
        self._pn = req_data.get('pn')

    def _serving_fn(self):
        search_request = self._create_text_query_request()
        return SearchRequest102(search_request).serve()

    def _create_text_query_request(self):
        claim = Patent(self._pn).first_claim
        query = utils.remove_claim_number(claim)
        search_request = self._data.copy()
        search_request['q'] = query
        search_request.pop('pn')
        return search_request

    def _validation_fn(self):
        if not utils.is_patent_number(self._data.get('pn')):
            raise BadRequestError(
                'Request does not contain a valid patent number.')

    def _formatting_fn(self, response):
        response['query'] = self._pn
        return response


class PatentPriorArtRequest(SimilarPatentsRequest):

    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        try:
            search_request = self._create_text_query_request()
            cutoff_date = Patent(self._pn).filing_date
            search_request['before'] = cutoff_date
        except:  # noqa: E722
            err_msg = f'Data unavailable for patent {self._pn}'
            raise ResourceNotFoundError(err_msg)
        return SearchRequest102(search_request).serve()


class DocumentRequest(APIRequest):

    _name = 'Document Request'

    def __init__(self, req_data):
        super().__init__(req_data)
        self._doc_id = req_data['id']

    def _validation_fn(self):
        if 'id' not in self._data:
            raise BadRequestError(
                'Request does not contain a document ID.')

    def _serving_fn(self):
        return Document(self._doc_id).json()


class PassageRequest(APIRequest):

    def __init__(self, req_data):
        super().__init__(req_data)
        self._query = req_data.get('q')
        self._doc_id = req_data.get('pn')
        self._doc = Document(self._doc_id)

    def _validation_fn(self):
        if not self._data.get('q'):
            raise BadRequestError(
                'Request does not contain a query.')
        if not self._data.get('pn'):
            raise BadRequestError(
                'Request does not specify a document.')


class SnippetRequest(PassageRequest):

    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        query = self._query
        text = self._doc.full_text
        return SnippetExtractor().extract_snippet(query, text)

    def _formatting_fn(self, snippet):
        return {
            'query': self._query,
            'id': self._doc_id,
            'snippet': snippet }


class MappingRequest(PassageRequest):

    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        query = self._query
        text = self._doc.full_text
        return generate_mapping(query, text)

    def _formatting_fn(self, mapping):
        return {
            'query': self._query,
            'id': self._doc_id,
            'mapping': mapping }


class DatasetSampleRequest(APIRequest):

    poc_dataset = PoC()

    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        name = self._data['dataset']
        if name.lower() != 'poc':
            raise ResourceNotFoundError(f'No dataset named {name}.')
        n = self._data['n']
        return self.poc_dataset[int(n)]

    def _validation_fn(self):
        if 'dataset' not in self._data:
            raise BadRequestError('Dataset name unspecified.')
        if 'n' not in self._data:
            raise BadRequestError('Sample number unspecified.')

    def _formatting_fn(self, sample):
        formatted = {}
        formatted['anc'] = self._format(sample['anc'])
        formatted['pos'] = self._format(sample['pos'])
        formatted['negs'] = [self._format(neg) for neg in sample['negs']]
        return formatted

    def _format(self, pn):
        patent = Patent(pn)
        return {
            'publicationNumber': patent.id,
            'title': patent.title,
            'abstract': patent.abstract
        }


class IncomingExtensionRequest(SearchRequest102):

    def __init__(self, req_data):
        if not allow_incoming_extension_requests:
            raise NotAllowedError(
                'Server does not accept extension requests.')
        else:
            super().__init__(req_data)


class AbstractPatentDataRequest(APIRequest):

    PN_PATTERN = r'^US(RE)?\d{4,11}[AB]\d?$'

    def __init__(self, req_data):
        super().__init__(req_data)
        self._pn = req_data['pn']
        self._patent = Patent(self._pn)

    def _validation_fn(self):
        if self._data['pn'][:2] != 'US':
            raise BadRequestError('Only US patents supported.')
        if not re.match(self.PN_PATTERN, self._data['pn']):
            raise BadRequestError('Could not parse patent number.')

    def _is_granted_patent(self):
        return len(self._pn) < 13

    def _formatting_fn(self, response):
        if isinstance(response, dict):
            response['pn'] = self._patent.publication_id
        return response


class AbstractDrawingRequest(AbstractPatentDataRequest):
    
    S3_BUCKET = s3.Bucket(PQAI_S3_BUCKET_NAME)
    PN_PATTERN = r'^US(RE)?\d{4,11}[AB]\d?$'

    def __init__(self, req_data):
        super().__init__(req_data)

    def _validation_fn(self):
        if self._data['pn'][:2] != 'US':
            raise BadRequestError('Only US patents supported.')
        if not re.match(self.PN_PATTERN, self._data['pn']):
            raise BadRequestError('Could not parse patent number.')

    def _get_prefix(self):
        number = self._get_8_digits() if self._is_granted_patent() else self._pn
        return f'images/{number}-'

    def _get_8_digits(self):
        pattern = r'(.+?)(A|B)\d?'
        digits = re.match(pattern, self._pn[2:])[1]    # extract digits
        if len(digits) == 7:
            digits = '0' + digits
        return digits


class DrawingRequest(AbstractDrawingRequest):

    def __init__(self, req_data):
        super().__init__(req_data)
        self._n = req_data['n']
        self._tmp_file = None
        self._local_file = None
        self._filename = None

    def _validation_fn(self):
        super()._validation_fn()
        if not re.match(r'\d+', str(self._data['n'])):
            raise BadRequestError('Drawing number should be integer.')

    def _serving_fn(self):
        self._download_file_from_s3()
        self._convert_to_jpg()
        return self._local_file

    def _download_file_from_s3(self):
        s3_prefix = self._get_prefix()
        s3_suffix = f'{self._n}.tif'
        s3_key = s3_prefix + s3_suffix
        filename_with_ext = s3_key.split('/')[-1]
        self._filename = filename_with_ext.split('.')[0]
        self._tmp_file = f'/tmp/{self._filename}.tif'
        try:
            self.S3_BUCKET.download_file(s3_key, self._tmp_file)
        except botocore.exceptions.ClientError:
            raise ResourceNotFoundError('Drawing unavailable.')

    def _convert_to_jpg(self):
        im = Image.open(self._tmp_file)
        self._local_file = f'/tmp/{self._filename}.jpg'
        im.convert("RGB").save(self._local_file, "JPEG", quality=50)
        os.remove(self._tmp_file)
        return self._local_file


class ListDrawingsRequest(AbstractDrawingRequest):

    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        prefix = self._get_prefix()
        indexes = [o.key.split('-')[-1].split('.')[0]
                     for o in self.S3_BUCKET.objects.filter(Prefix=prefix)]
        return {'drawings': indexes}


class PatentDataRequest(AbstractPatentDataRequest):

    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        patent_data = {
            'title': self._patent.title,
            'abstract': self._patent.abstract,
            'description': self._patent.description,
            'claims': self._patent.claims,
            'publication_date': self._patent.publication_date,
            'filing_date': self._patent.filing_date
        }
        return patent_data


class TitleRequest(AbstractPatentDataRequest):

    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        return {'title': self._patent.title}


class AbstractRequest(AbstractPatentDataRequest):

    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        return {'abstract': self._patent.abstract}


class AllClaimsRequest(AbstractPatentDataRequest):

    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        return {'claims': self._patent.claims}


class OneClaimRequest(AbstractPatentDataRequest):

    def __init__(self, req_data):
        super().__init__(req_data)
        self._n = int(req_data['n'])

    def _validation_fn(self):
        super()._validation_fn()
        if 'n' not in self._data:
            raise BadRequestError('Claim number unspecified.')
        if not re.match(r'^\d+$', self._data['n']):
            raise BadRequestError('Claim number should be integer')
        if int(self._data['n']) < 1:
            raise BadRequestError('Claim number cannot be <= 0')

    def _serving_fn(self):
        if self._n > len(self._patent.claims):
            raise ResourceNotFoundError(f'{self._pn} has no claim #{self._n}')
        return {
            'claim': self._patent.claims[self._n-1],
            'claim_num': self._n
        }


class IndependentClaimsRequest(AbstractPatentDataRequest):

    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        return {'claims': self._patent.independent_claims}


class PatentDescriptionRequest(AbstractPatentDataRequest):

    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        return {'description': self._patent.description}


class CitationsRequest(AbstractPatentDataRequest):

    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        back_cits = self._patent.backward_citations
        for_cits = self._patent.forward_citations
        return {
            'citations_backward': back_cits,
            'citations_forward': for_cits
        }


class BackwardCitationsRequest(AbstractPatentDataRequest):

    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        cits = self._patent.backward_citations
        return {'citations_backward': cits}


class ForwardCitationsRequest(AbstractPatentDataRequest):

    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        cits = self._patent.forward_citations
        return {'citations_forward': cits}


class ConceptsRequest(APIRequest):

    def __init__(self, req_data):
        super().__init__(req_data)
        self._text = req_data['text']

    def _validation_fn(self):
        if not isinstance(self._data['text'], str):
            raise BadRequestError('Invalid text.')
        if not self._data['text'].strip():
            raise BadRequestError('No text to work with.')

    def _serving_fn(self):
        return list(default_boe_encoder.encode(self._text))


class AbstractConceptsRequest(AbstractPatentDataRequest):

    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        req = ConceptsRequest({'text': self._patent.abstract})
        concepts = req.serve()
        return {'concepts': concepts}


class DescriptionConceptsRequest(AbstractPatentDataRequest):

    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        req = ConceptsRequest({'text': self._patent.description})
        concepts = req.serve()
        return {'concepts': concepts}


class CPCsRequest(AbstractPatentDataRequest):

    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        return {'cpcs': self._patent.cpcs}


class ListThumbnailsRequest(ListDrawingsRequest):

    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        thumbnails = super()._serving_fn()['drawings']
        return {'thumbnails': thumbnails}


class ThumbnailRequest(DrawingRequest):

    DEFAULT_HEIGHT = 200

    def __init__(self, req_data):
        super().__init__(req_data)
        self._h = req_data.get('h')
        self._w = req_data.get('w')
        self._h = None if self._h is None else int(self._h)
        self._w = None if self._w is None else int(self._w)
        if self._h is None and self._w is None:
            self._h = self.DEFAULT_HEIGHT

    def _validation_fn(self):
        super()._validation_fn()
        for dimension in ('w', 'h'):
            if self._data.get(dimension) is None:
                continue
            if not re.match(r'^\d+$', str(self._data[dimension])):
                raise BadRequestError('Thumbnail size must be an integer')
            elif int(self._data[dimension]) > 800:
                raise BadRequestError('Thumbnail dimensions must be <= 800')

    def _serving_fn(self):
        im_path = super()._serving_fn()
        im = cv2.imread(im_path)
        im = self._downscale(im)
        cv2.imwrite(im_path, im) # Overwrite the original
        return im_path

    def _downscale(self, im):
        h, w = self._get_out_dims(im)
        im = cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA)
        return im

    def _get_out_dims(self, im):
        h, w, channels = im.shape
        r = w / h
        if isinstance(self._h, int) and isinstance(self._w, int):
            return (self._h, self._w)
        elif isinstance(self._h, int):
            width = max(1, int(self._h*r))
            return (self._h, width)
        elif isinstance(self._w, int):
            height = max(1, int(self._w/r))
            return (height, self._w)
        else:
            return (h, w)


class PatentCPCVectorRequest(AbstractPatentDataRequest):

    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        cpcs = self._patent.cpcs
        vector = CPCVectorizer().embed(cpcs)
        return {'vector': vector.tolist()}


class PatentAbstractVectorRequest(AbstractPatentDataRequest):

    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        abstract = self._patent.abstract
        vector = SentBERTVectorizer().embed(abstract)
        return {'vector': vector.tolist()}


class ConceptRelatedRequest(APIRequest):

    def __init__(self, req_data):
        super().__init__(req_data)
        self._concept = req_data['concept'].lower()

    def _validation_fn(self):
        if not isinstance(self._data['concept'], str):
            raise BadRequestError('Concept must be a string.')
        if not self._data['concept'].strip():
            raise BadRequestError('Null string provided as concept')

    def _formatting_fn(self, response):
        if isinstance(response, dict):
            response['concept'] = self._concept
        return response


class SimilarConceptsRequest(ConceptRelatedRequest):

    LIMIT = 100 # max similar concepts that can be returned

    def __init__(self, req_data):
        super().__init__(req_data)
        self._n = int(self._data.get('n', 10))
        self._n = min(self._n, self.LIMIT)

    def _serving_fn(self):
        if self._concept not in default_embedding_matrix:
            raise ResourceNotFoundError(f'No vector for "{self._concept}"')

        n = 2*self._n  # because some will be filtered out
        neighbours = default_embedding_matrix.similar_to_item(self._concept, n)
        neighbours = [e for e in neighbours if self._concept not in e][:self._n]
        return {'similar': neighbours}


class ConceptVectorRequest(ConceptRelatedRequest):

    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        if self._concept not in default_embedding_matrix:
            raise ResourceNotFoundError(f'No vector for "{self._concept}"')

        vector = default_embedding_matrix[self._concept]
        return {'vector': list(vector)}


class DocumentationRequest(APIRequest):

    def __init__(self, req_data):
        super().__init__(req_data)
        self._template_file = f'{docs_dir}template.html'
        self._docs_file = f'{docs_dir}README-API.md'

    def _serving_fn(self):
        template = self._get_template()
        contents = self._get_docs_html()
        template.find('body').append(contents)
        return str(template)

    def _get_template(self):
        with open(self._template_file, 'r') as f:
            html = f.read()
        return BeautifulSoup(html, 'html.parser')

    def _get_docs_html(self):
        with open(self._docs_file, 'r') as f:
            md = f.read()
        exts = ['tables', 'toc', 'smarty', 'codehilite']
        html = markdown.markdown(md, extensions=exts)
        return BeautifulSoup(html, 'html.parser')


class AggregatedCitationsRequest(AbstractPatentDataRequest):

    LIMIT = 10000

    def __init__(self, req_data):
        super().__init__(req_data)
        self._n = int(req_data['levels'])
        if req_data.get('fanout'):
            self._fanout_limit = int(req_data['fanout'])
        else:
            self._fanout_limit = math.inf # no limit

    def _serving_fn(self):
        cits = set([self._pn])
        for i in range(self._n):
            for c in cits:
                if len(cits) > self.LIMIT:
                    raise ServerError('Too many citations, try lower levels')
                try:
                    patent = Patent(c)
                    if len(patent.backward_citations) <= self._fanout_limit or i == 1:
                        cits = cits.union(set(patent.backward_citations))
                    if len(patent.forward_citations) <= self._fanout_limit or i == 1:
                        cits = cits.union(set(patent.forward_citations))

                except: # noqa: E722
                    continue
        cits.remove(self._pn)
        return list(cits)

    def _validation_fn(self):
        super()._validation_fn()
        self._check_levels_param()
        self._check_fanout_param()

    def _check_levels_param(self):
        self._check_levels_param_exists()
        self._check_levels_param_is_valid()

    def _check_levels_param_exists(self):
        levels = self._data.get('levels')
        if levels is None :
            raise BadRequestError('Expected a levels parameter')

    def _check_levels_param_is_valid(self):
        levels = self._data.get('levels')
        if isinstance(levels, str): # coming from web api
            if not re.match(r'^\d+$', levels):
                raise BadRequestError('Invalid levels value')
        n = int(levels)
        if n < 1 or n > 4:
            raise BadRequestError('Levels should be in range [1, 4]')

    def _check_fanout_param(self):
        if self._data.get('fanout'):
            if not re.match(r'^\d+$', self._data['fanout']):
                raise BadRequestError('Invalid fanout value')
