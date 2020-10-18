from core.vectorizers import SentBERTVectorizer
from core.index_selection import SublassesBasedIndexSelector
from core.filters import FilterArray, PublicationDateFilter, DocTypeFilter
from core.obvious import Combiner
from core.indexes import IndexesDirectory
from core.search import VectorIndexSearcher
from core.documents import Document
from core.snippet import SnippetExtractor
from core.reranking import ConceptMatchRanker
from config.config import indexes_dir, reranker_active

vectorize_text = SentBERTVectorizer().embed
available_indexes = IndexesDirectory(indexes_dir)
select_indexes = SublassesBasedIndexSelector(available_indexes).select
vector_search = VectorIndexSearcher().search
extract_snippet = SnippetExtractor.extract_snippet
generate_mapping = SnippetExtractor.map
reranker = None if not reranker_active else ConceptMatchRanker()


class APIRequest():
    
    def __init__(self, req_data=None):
        self._data = req_data

    def serve(self):
        self._raise_if_invalid()
        return self._serving_fn()

    def _raise_if_invalid(self):
        if not self._validation_fn():
            raise Exception('Invalid request data.')

    def _serving_fn(self):
        pass

    def _validation_fn(self):
        return True


class SearchRequest(APIRequest):

    def __init__(self, req_data):
        super().__init__(req_data)
        self._query = req_data.get('q', '')
        self._latent_query = req_data.get('lq', '')
        self._n_results = int(req_data.get('n', 10))
        self._full_query = self._get_full_query()
        self._indexes = self._get_indexes()
        self._need_snippets = self._read_bool_value('snip')
        self._need_mappings = self._read_bool_value('maps')
        self._filters = FilterExtractor(self._data).extract()
        self.MAX_RES_LIMIT = 100

    def _serving_fn(self):
        results = self._searching_fn()
        return self._formatting_fn(results)

    def _searching_fn(self):
        pass

    def _get_full_query(self):
        return (self._query + '\n' + self._latent_query).strip()

    def _get_indexes(self):
        if self._index_specified_in_request():
            index_in_req = self._data['idx']
            indexes = available_indexes.get(index_in_req)
        else:
            indexes = select_indexes(self._full_query, 3)
        return indexes

    def _index_specified_in_request(self):
        req_data = self._data
        if not 'idx' in req_data:
            return False
        if req_data['idx'] == 'auto':
            return False
        return True

    def _add_snippet_if_needed(self, result):
        if self._need_snippets:
            result.snippet = extract_snippet(self._query, result.full_text)

    def _add_mapping_if_needed(self, result):
        if self._need_mappings:
            result.mapping = generate_mapping(self._query, result.full_text)

    def _read_bool_value(self, key):
        val = self._data.get(key)
        if ((isinstance(val, str) and val in ['true', '1', 'yes']) or
            (isinstance(val, int) and val != 0)):
            return True
        return False


class FilterExtractor():

    def __init__(self, req_data):
        self._data = req_data

    def extract(self):
        filters = FilterArray()
        date_filter = self._get_date_filter()
        doctype_filter = self._get_doctype_filter()
        if date_filter:
            filters.add(date_filter)
        if doctype_filter:
            filters.add(doctype_filter)
        return filters

    def _get_date_filter(self):
        after = self._data.get('after', None)
        before = self._data.get('before', None)
        if after or before:
            after = None if not bool(after) else after
            before = None if not bool(before) else before
            return PublicationDateFilter(after, before)

    def _get_doctype_filter(self):
        doctype = self._data.get('type')
        if doctype:
            return DocTypeFilter(doctype)


class SearchRequest102(SearchRequest):

    def __init__(self, req_data):
        super().__init__(req_data)

    def _searching_fn(self):
        n = self._n_results
        qvec = vectorize_text(self._full_query)
        results = []
        m = n
        m *= 4 # find more results than needed for effective reranking
        while len(results) < n and m < self.MAX_RES_LIMIT:
            results = vector_search(qvec, self._indexes, m)
            results = self._filters.apply(results)
            m *= 2
        if reranker:
            result_texts = [r.full_text for r in results]
            ranks = reranker.rank(self._query, result_texts)
            print(ranks)
            results = [results[i] for i in ranks]
        return results[:n]

    def _formatting_fn(self, results):
        for result in results:
            self._add_snippet_if_needed(result)
            self._add_mapping_if_needed(result)
        return {
            'results': [res.json() for res in results],
            'query': self._query,
            'latent_query': self._latent_query,
            'n_results': self._n_results,
            'snippets_included': self._need_snippets,
            'mappings_included': self._need_mappings
        }


class SearchRequest103(SearchRequest):
    
    def __init__(self, req_data):
        super().__init__(req_data)

    def _searching_fn(self):
        docs = self._get_docs_to_combine()
        abstracts = [doc.abstract for doc in docs]
        combiner = Combiner(self._query, abstracts)
        index_pairs = combiner.get_combinations(self._n_results)
        combinations = [(docs[i], docs[j]) for i, j in index_pairs]
        return combinations

    def _get_docs_to_combine(self):
        interim_req_data = self._data.copy()
        interim_req_data['n'] = 100
        interim_req = SearchRequest102(self._data)
        interim_results = interim_req.serve()['results']
        docs = [Document(res['id']) for res in interim_results]
        return docs

    def _formatting_fn(self, combinations):
        for comb in combinations:
            for result in comb:
                self._add_snippet_if_needed(result)
                self._add_mapping_if_needed(result)
        return {
            'results': [[r.json() for r in comb] for comb in combinations],
            'query': self._query,
            'latent_query': self._latent_query,
            'n_results': self._n_results,
            'snippets_included': self._need_snippets,
            'mappings_included': self._need_mappings
        }


class PassageRequest(APIRequest):

    def __init__(self, req_data):
        super().__init__(req_data)
        self._query = req_data.get('q')
        self._doc_id = req_data.get('pn')
        self._doc = Document(self._doc_id)

    def _validation_fn(self):
        if not self._query or not self._doc_id:
            return False
        return True


class SnippetRequest(PassageRequest):

    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        query = self._query
        text = self._doc.full_text
        return extract_snippet(query, text)

    def _formatting_fn(self, snippet):
        return {
            'query': self._query,
            'id': self._doc_id,
            'snippet': snippet,
        }


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
            'mapping': mapping,
        }
