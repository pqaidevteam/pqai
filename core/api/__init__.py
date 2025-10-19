import os, re, json, time, threading, traceback  # noqa: E401
import cv2
import markdown
import boto3
import botocore.exceptions
from bs4 import BeautifulSoup
from PIL import Image
import numpy as np
from pydantic import BaseModel, ValidationError, Field
from typing import Optional

from core.vectorizers import SentBERTVectorizer
from core.index_selection import SubclassBasedIndexSelector
from core.filters import FilterExtractor
from core.obvious import Combiner
from core.indexes import IndexesDirectory
from core.documents import Document, Patent
from core.snippet import SnippetExtractor
from core.reranking import ConceptMatchRanker
from core.encoders import default_boe_encoder, default_embedding_matrix
from core.results import SearchResult
import core.remote as remote
import core.utils as utils
from .errors import (
    BadRequestError,
    ResourceNotFoundError,
    ServerError,
    NotAllowedError
)
from services import vector_search as vector_search_srv

from config.config import (
    indexes_dir,
    reranker_active,
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
    _schema = None
    
    def __init__(self, req_data=None):
        if self._schema:
            try:
                validated = self._schema(**req_data)
                self._data = validated.model_dump()
            except ValidationError as e:
                raise BadRequestError(str(e))
        else:
            self._data = req_data or {}

    def serve(self):
        try:
            response = self._serve()
            return self._format(response)
        except BadRequestError as e:
            raise e
        except ResourceNotFoundError as e:
            raise e
        except Exception:
            traceback.print_exc()
            raise ServerError()

    def _serve(self):
        raise NotImplementedError()

    def _format(self, response):
        return response

class SearchRequestSchema(BaseModel):
    q: str = Field(min_length=1)
    lq: str = Field(default='')
    offset: int = Field(default=0, ge=0)
    n: int = Field(default=10, ge=1, le=500)
    type: str = Field(default='patent', pattern=r'^(patent|npl|any)$')
    idx: Optional[str] = Field(default=None)
    snip: bool = Field(default=False)
    maps: bool = Field(default=False)
    after: Optional[str] = Field(default=None)
    before: Optional[str] = Field(default=None)
    dtype: str = Field(default='priority', pattern=r'^(publication|filing|priority)$')

class SearchRequest(APIRequest):
    _schema = SearchRequestSchema
    MAX_RES_LIMIT = 500
    MIN_SIMILARITY_THRESHOLD = 0.5

    def __init__(self, req_data):
        super().__init__(req_data)
        self._query = self._data.get('q')
        self._latent_query = self._data.get('lq')

        self._offset = self._data.get('offset')
        self._n_results = self._data.get('n')
        self._n_results += self._offset # for pagination

        self._doctype = self._data.get('type')

        self._filters = FilterExtractor.extract(self._data)
        self._indexes = self._get_indexes()

    def _serve(self):
        raise NotImplementedError()

    def _get_indexes(self):
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
    
    def _format(self, results):
        arr = []
        for result in results:
            if isinstance(result, SearchResult):
                self._format_result(result)
                arr.append(result.json())
            else:
                for r in result:
                    self._format_result(r)
                arr.append([r.json() for r in result])
        return {
            'results': arr,
            'query': self._query,
            'latent_query': self._latent_query
        }
    
    def _format_result(self, result):
        if self._data.get('maps'):
            try:
                result.mapping = generate_mapping(self._query, result.full_text)
            except Exception:
                result.mapping = None
        if self._data.get('snip'):
            try:
                result.snippet = SnippetExtractor.extract_snippet(self._query, result.full_text)
            except Exception:
                result.snippet = None
        if result.type == 'patent':
            result.image = f'https://api.projectpq.ai/patents/{result.id}/thumbnails/1'


class SearchRequest102(SearchRequest):

    def _serve(self):
        results = self._search()
        if self._n_results < 100:
            results = self._rerank(results)
        results = results[:self._n_results]
        return results[self._offset:]

    def _search(self):
        query = re.sub(r'\`(\-[\w\*\?]+)\`', '', self._query)
        query = re.sub(r"\`", "", query)
        qvec = vectorize_text("[query] " + query)
        relevant, irrelevant = self._extract_feedback(self._latent_query)
        if relevant or irrelevant: # user feedback
            qvec = self._update_search_vector(qvec, relevant, irrelevant)

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
        results = [SearchResult(*t) for t in results]
        results = self._deduplicate(results)
        return results[:n]

    def _update_search_vector(self, qvec, relevant, irrelevant):
        alpha = 1.0
        beta = 1.0
        gamma = 1.0

        if relevant:
            vr = np.array([vectorize_text(Patent(pn).abstract) for pn in relevant])
            vr_mean = np.mean(vr, axis=0)
            qvec = alpha*qvec + beta*vr_mean
        
        if irrelevant:
            vi = np.array([vectorize_text(Patent(pn).abstract) for pn in irrelevant])
            vi_mean = np.mean(vi, axis=0)
            qvec = qvec - gamma*vi_mean
        
        qvec = qvec / np.linalg.norm(qvec)
        return qvec
    
    def _extract_feedback(self, latent_query):
        try:
            lq_data = json.loads(latent_query)
        except Exception:
            return [], []
        
        if not isinstance(lq_data, dict):
            return [], []
        
        relevant = lq_data.get('relevant', [])
        irrelevant = lq_data.get('irrelevant', [])
        return relevant, irrelevant

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
            diff_score = abs(last[2] - this[2])
            if  diff_score >= epsilon:
                output.append(this)
                continue
            
            # when scores are too close (likely family members), prefer an English-language member
            cc_this = this[0][:2]
            cc_last = last[0][:2]
            cc_pref = ['US', 'EP', 'GB', 'CA', 'AU', 'WO', 'SG', 'IN'] # native English abstracts
            cc_rank = {cc: i for i, cc in enumerate(cc_pref)}
            default_rank = len(cc_pref)
            if cc_this == cc_last:
                continue

            rank_this = cc_rank.get(cc_this, default_rank)
            rank_last = cc_rank.get(cc_last, default_rank)
            if rank_this < rank_last:
                output[-1] = this

        return output

    def _deduplicate(self, results):
        relevant, irrelevant = self._extract_feedback(self._latent_query)
        seen = set(relevant + irrelevant)
        results = [r for r in results if r.id not in seen]

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


class SearchRequest103(SearchRequest):

    def _serve(self):
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
        params = {**self._data, 'n': 100, 'offset': 0, 'snip': 0, 'maps': 0}
        results = SearchRequest102(params).serve()['results']
        return [SearchResult(r['id'], r['index'], r['score']) for r in results]


class SearchRequestCombined102and103(SearchRequest103):

    def _serve(self):
        results103 = super()._search()
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


class SimilarPatentsRequest(APIRequest):

    def _serve(self):
        search_request = self._create_text_query_request()
        return SearchRequest102(search_request).serve()

    def _create_text_query_request(self):
        pn = self._data.get('pn')
        claim = Patent(pn).first_claim
        query = utils.remove_claim_number(claim)
        search_request = {'q': query}
        return search_request

    def _validation_fn(self):
        if not utils.is_patent_number(self._data.get('pn')):
            raise BadRequestError(
                'Request does not contain a valid patent number.')

    def _format(self, response):
        response['query'] = self._data.get('pn')
        return response


class PatentPriorArtRequest(SimilarPatentsRequest):

    def _serve(self):
        pn = self._data.get('pn')
        try:
            cutoff_date = Patent(pn).filing_date
            search_request = self._create_text_query_request()
            search_request['before'] = cutoff_date
        except Exception:  # noqa: E722
            err_msg = f'Data unavailable for patent {pn}'
            raise ResourceNotFoundError(err_msg)
        return SearchRequest102(search_request).serve()

class DocumentRequestSchema(BaseModel):
    id: str = Field(min_length=1)

class DocumentRequest(APIRequest):
    _schema = DocumentRequestSchema

    def __init__(self, req_data):
        super().__init__(req_data)
        self._doc_id = req_data['id']

    def _serve(self):
        doc_id = self._data.get('id')
        return Document(doc_id).json()

class PassageRequestSchema(BaseModel):
    q: str = Field(min_length=1)
    pn: str = Field(min_length=1)

class PassageRequest(APIRequest):
    _schema = PassageRequestSchema

    def __init__(self, req_data):
        super().__init__(req_data)
        self._query = req_data.get('q')
        self._doc_id = req_data.get('pn')
        self._doc = Document(self._doc_id)
        self._text = self._doc.full_text
    
    def _format(self, response):
        return {
            'query': self._data.get('q'),
            'id': self._data.get('pn'),
            **response
        }

class SnippetRequest(PassageRequest):

    def _serve(self):
        snippet = SnippetExtractor().extract_snippet(self._query, self._text)
        return {"snippet": snippet}

class MappingRequest(PassageRequest):

    def _serve(self):
        mapping = generate_mapping(self._query, self._text)
        return {"mapping": mapping}

class IncomingExtensionRequest(SearchRequest102):

    def __init__(self, req_data):
        if not allow_incoming_extension_requests:
            msg = 'This server does not accept extension requests.'
            raise NotAllowedError(msg)
        else:
            super().__init__(req_data)

class PatentDataRequestSchema(BaseModel):
    pn: str = Field(pattern=r'^US(RE)?\d{4,11}[AB]\d?$')
    fields: Optional[str] = Field(default=None)

class PatentDataRequest(APIRequest):

    _schema = PatentDataRequestSchema

    def __init__(self, req_data):
        super().__init__(req_data)
        self._pn = req_data['pn']
        self._patent = Patent(self._pn)

    def _serve(self):
        patent_data = {
            'pn': self._patent.publication_id,
            'title': self._patent.title,
            'abstract': self._patent.abstract,
            'description': self._patent.description,
            'claims': self._patent.claims,
            'independent_claims': self._patent.independent_claims,
            'publication_date': self._patent.publication_date,
            'filing_date': self._patent.filing_date,
            'priority_date': self._patent.priority_date,
            'inventors': self._patent.inventors,
            'assignees': self._patent.assignees,
            'cpcs': self._patent.cpcs,
            'citations_backward': self._patent.backward_citations,
            'citations_forward': self._patent.forward_citations
        }
        if self._data.get('fields'):
            fields = [f.strip().lower() for f in self._data['fields'].split(',')]
            patent_data = {k: v for k, v in patent_data.items() if k in fields}
        return patent_data

class DrawingRequestSchema(PatentDataRequestSchema):
    pn: str = Field(pattern=r'^US(RE)?\d{4,11}[AB]\d?$')
    n: Optional[int] = Field(default=1)
    w: Optional[int] = Field(default=None, ge=1, le=800)
    h: Optional[int] = Field(default=None, ge=1, le=800)


class DrawingRequest(APIRequest):
    _schema = DrawingRequestSchema

    S3_BUCKET = s3.Bucket(PQAI_S3_BUCKET_NAME)
    PN_PATTERN = r'^US(RE)?\d{4,11}[AB]\d?$'

    def _serve(self):
        tif_filepath = self._download_file_from_s3()
        jpg_filepath = self._convert_to_jpg(tif_filepath)

        if self._data.get('h') or self._data.get('w'):
            im = cv2.imread(jpg_filepath)
            im = self._downscale(im)
            cv2.imwrite(jpg_filepath, im)

        return jpg_filepath

    def _download_file_from_s3(self):
        s3_prefix = self._get_prefix()
        n = self._data.get('n')
        s3_suffix = str(n) + '.tif'
        s3_key = s3_prefix + s3_suffix
        filename_with_ext = s3_key.split('/')[-1]
        self._filename = filename_with_ext.split('.')[0]
        filepath = f'/tmp/{self._filename}.tif'
        try:
            self.S3_BUCKET.download_file(s3_key, filepath)
            return filepath
        except botocore.exceptions.ClientError:
            raise ResourceNotFoundError('Drawing unavailable.')

    def _convert_to_jpg(self, infilepath):
        im = Image.open(infilepath)
        filepath = f'/tmp/{self._filename}.jpg'
        im.convert("RGB").save(filepath, "JPEG", quality=50)
        os.remove(infilepath)
        return filepath
    
    def _downscale(self, im):
        h, w = self._get_out_dims(im)
        im = cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA)
        return im

    def _get_out_dims(self, im):
        h, w, channels = im.shape
        r = w / h
        h_ = self._data.get('h')
        w_ = self._data.get('w')
        if h_ is None and w_ is None:
            return (h, w)
        if isinstance(h_, int) and isinstance(w_, int):
            return (h_, w_)
        elif isinstance(h_, int):
            width = max(1, int(h_*r))
            return (h_, width)
        elif isinstance(w_, int):
            height = max(1, int(w_/r))
            return (height, w_)
        else:
            return (h, w)
    
    def _get_prefix(self):
        number = self._get_8_digits() if self._is_granted_patent() else self._data.get('pn')
        return f'images/{number}-'

    def _get_8_digits(self):
        pattern = r'(.+?)(A|B)\d?'
        digits = re.match(pattern, self._data.get('pn')[2:])[1]    # extract digits
        if len(digits) == 7:
            digits = '0' + digits
        return digits
    
    def _is_granted_patent(self):
        return len(self._data.get('pn')) < 13


class ListDrawingsRequest(DrawingRequest):

    def _serve(self):
        prefix = self._get_prefix()
        indexes = [o.key.split('-')[-1].split('.')[0]
                     for o in self.S3_BUCKET.objects.filter(Prefix=prefix)]
        return {
            'drawings': indexes,
            'thumbnails': indexes
        }

class ConceptsRequest(APIRequest):

    def __init__(self, req_data):
        super().__init__(req_data)
        self._text = req_data['text']

    def _validation_fn(self):
        if not isinstance(self._data['text'], str):
            raise BadRequestError('Invalid text.')
        if not self._data['text'].strip():
            raise BadRequestError('No text to work with.')

    def _serve(self):
        return list(default_boe_encoder.encode(self._text))


class AbstractConceptsRequest(PatentDataRequest):

    def _serve(self):
        req = ConceptsRequest({'text': self._patent.abstract})
        concepts = req.serve()
        return {'concepts': concepts}


class DescriptionConceptsRequest(PatentDataRequest):

    def _serve(self):
        req = ConceptsRequest({'text': self._patent.description})
        concepts = req.serve()
        return {'concepts': concepts}


class PatentAbstractVectorRequest(PatentDataRequest):

    def _serve(self):
        abstract = self._patent.abstract
        vector = SentBERTVectorizer().embed(abstract)
        return {'vector': vector.tolist()}

class ConceptRelatedRequestSchema(BaseModel):
    concept: str = Field(min_length=1)

class ConceptRelatedRequest(APIRequest):
    _schema = ConceptRelatedRequestSchema

    def __init__(self, req_data):
        super().__init__(req_data)
        self._concept = req_data['concept'].lower()

    def _format(self, response):
        if isinstance(response, dict):
            response['concept'] = self._concept
        return response


class SimilarConceptsRequest(ConceptRelatedRequest):

    LIMIT = 100 # max similar concepts that can be returned

    def __init__(self, req_data):
        super().__init__(req_data)
        self._n = int(self._data.get('n', 10))
        self._n = min(self._n, self.LIMIT)

    def _serve(self):
        if self._concept not in default_embedding_matrix:
            raise ResourceNotFoundError(f'No vector for "{self._concept}"')

        n = 2*self._n  # because some will be filtered out
        neighbours = default_embedding_matrix.similar_to_item(self._concept, n)
        neighbours = [e for e in neighbours if self._concept not in e][:self._n]
        return {'similar': neighbours}


class ConceptVectorRequest(ConceptRelatedRequest):

    def _serve(self):
        if self._concept not in default_embedding_matrix:
            raise ResourceNotFoundError(f'No vector for "{self._concept}"')

        vector = default_embedding_matrix[self._concept]
        return {'vector': list(vector)}


class DocumentationRequest(APIRequest):
    _template_file = f'{docs_dir}template.html'
    _docs_file = f'{docs_dir}README-API.md'

    def _serve(self):
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

