from core import utils
from core import db
from core.indexes import index_ids as AVAILABLE_INDEXES
from core.indexes import get_index
from core.documents import Document
from dateutil.parser import parse as parse_date
from core.classifiers import BOWSubclassPredictor, BERTSubclassPredictor 

predict_subclasses = BERTSubclassPredictor().predict_subclasses

N_INDEXES_TO_SEARCH = 3
MAX_RESULTS_LIMIT = 200


class Searcher():

	"""A wrapper for putting search parameters and associated conditions
	in a coherent manner. A searcher is defined by a number of settings,
	e.g., the number of results to return and what type of documents
	they should be, which indexes are to be searched, and the re-ranking
	algorithms to be used, etc.
	
	Searcher interfaces with the outside world by its `run` method.
	Before calling this method, all parameters should be set.

	Exemplary usage
	================

	searcher = Searcher()
	searcher.result_count = 10
	searcher.return_snippets = False
	searcher.return_mappings = True
	searcher.search_with_preamble = False
	searcher.filter = None
	search.indexes = ['H04W.abs', 'H04W.ttl']
	search.reranker = None
	results = searcher.search('wireless communication device')
	results = searcher.search('US10112730B2')

	"""
	
	def __init__(self):
		self._result_count = 10
		self._return_snippets = False
		self._return_mappings = False
		self._search_with_preamble = False
		self._filter = None
		self._index_selector = None
		self._indexes = None
		self._reranking_fn = None
		self._max_results = 100
		self._snippet_extractor_fn = None

	@property
	def result_count(self):
		return self._result_count
	
	@result_count.setter
	def result_count(self, n):
		self._result_count = n

	@property
	def return_snippets(self):
		return self._return_snippets

	@return_snippets.setter
	def return_snippets(self, value):
		self._return_snippets = value

	@property
	def return_mappings(self):
		return self._return_mappings

	@return_mappings.setter
	def return_mappings(self, value):
		self._return_mappings = value

	@property
	def search_with_preamble(self):
		return self._search_with_preamble

	@search_with_preamble.setter
	def search_with_preamble(self, value):
		self._search_with_preamble = value
	
	@property
	def filter(self):
		return self._filter

	@filter.setter
	def filter(self, value):
		self._filter = value

	@property
	def indexes(self):
		return self._indexes
	
	@indexes.setter
	def indexes(self, index_ids):
		self._indexes = [get_index(index_id) for index_id in index_ids]

	@property
	def index_selector(self):
		return self._index_selector

	@index_selector.setter
	def index_selector(self, fn):
		self._index_selector = fn

	@property
	def reranker(self):
		return self._reranking_fn

	@reranker.setter
	def reranker(self, fn):
		self._reranking_fn = fn

	@property
	def max_results(self):
		return self._max_results
	
	@max_results.setter
	def max_results(self, value):
		self._max_results = value

	@property
	def snippet_extractor(self):
		return self._snippet_extractor_fn
	
	@max_results.setter
	def snippet_extractor(self, fn):
		self._snippet_extractor_fn = fn

	def run (self, query, latent_query=None):
		"""Run the query.
		
		Args:
		    query (str): Either a long-form query or a document ID, e.g.
		 		a patent number
		    latent_query (None, optional): A latent query for context
		
		Returns:
		    list: A sequence of `SearchResult` objects
		"""
		if utils.is_doc_id(query):
			search_fn = self._search_by_doc_id
		else:
			search_fn = self._search_by_text
		return search_fn(query, latent_query)

	def _get_indexes(self, query=None):
		"""Get a list of `Index` objects that will be searched for matches.
		
		Args:
		    query (str, Optional): The text query on the basis of which
		    	suitable indexes may be selected automatically. 
		
		Returns:
		    list: A sequence of `Index` objects
		
		Raises:
		    Exception: Raised when no index can be selected because
		    	neither they have been specified explcitly nor can they
		    	be selected on the basis of the query (either because
		    	the query itself has not been supplied or any index
		    	selector function hasn't been specified)
		"""
		if self.indexes:
			return self.indexes

		if callable(self.index_selector):
			if not query:
				raise Exception('A valid query is required for \
					selecting indexes automatically, however, it has \
					not been supplied')
			return self.index_selector(query)

		raise Exception('Indexes must be explicity specified or \
			an index selector function must be specified for the \
			`Searcher` before it can run queries.')

	def _search_by_text(self, query, latent_query=None):
		results = self._get_results(query, latent_query)

		# Results may be more numerous than needed
		results = results[:self.result_count]

		if self.reranker:
			self._rerank(results, query)
		if self.return_snippets:
			self._add_snippets(results, query)
		if self.return_mappings:
			self._add_mappings(results, query)

		results = self._deduplicate(results)
		return results

	def _deduplicate(self, results):
		ids = set([])
		deduplicated = []
		for result in results:
			if not result.id in ids:
				ids.add(result.id)
				deduplicated.append(result)
		return deduplicated

	def _get_results(self, querytext, latent_query=None):
		"""Actually run the query through the indexes and apply filters
		to get a list of results matching the query and satisfying the
		filter conditions.
		
		Args:
		    querytext (str): Query
		    latent_query (None, optional): Optional query for context
		
		Returns:
		    list: Sequence of `SearchResult` objects
		"""
		indexes = self._get_indexes(querytext)
		n = self.result_count
		results = []
		while len(results) < self.result_count and n < self.max_results:
			id_score_pairs = [res for idx in indexes
						for res in idx.run_text_query(querytext, n, True)]
			id_score_pairs.sort(key=lambda x: x[1], reverse=True)
			results = [SearchResult(res, score) for res, score in id_score_pairs]
			results = self._apply_filter(results)
			n *= 2

		return results

	def _search_by_doc_id(self, doc_id, latent_query=None):
		"""Search by considering the document as a query. Features shall
		be extracted from the document to create a text query.
		
		Args:
		    doc_id (str): Document ID, e.g., a patent number
		    latent_query (None, optional): Optional query for context
		
		Returns:
		    list: A sequence of `SearchResult` objects
		"""
		textquery = utils.text_query_from_doc(doc_id)
		return self._search_by_text(textquery, latent_query)

	def _apply_filter(self, results):
		"""Return results that satisfy the filter conditions.
		
		Args:
		    results (list): Sequence of `SearchResult` instances.
		
		Returns:
		    list: A sub-sequence of the input results which satisfy the
		    	filter condition.
		"""
		if self.filter is None:
			return results
		return [res for res in results if self.filter.apply(res)]

	def _rerank(self, results, query):
		"""Rerank the results (in place update of results list).
		
		Args:
		    results (list): Instances of `SearchResult`
		    query (str): Query text
		"""
		if callable(self._reranking_fn):
			results = self._reranking_fn(results, query)

	def _add_snippets(self, results, query):
		"""Add a snippet to each result (in place update).
		
		Args:
		    results (list): Instances of `SearchResult`
		    query (str): Query text
		
		Raises:
		    Exception: Raised when no snippet extraction function has
		    	been specified.
		"""
		if not callable(self._snippet_extractor_fn):
			raise Exception('Searcher has invalid configuration. It is \
				configured to return snippets but any snippet \
				extraction function has not been specified.')
		for result in results:
			text = result.full_text
			result.snippet = self._snippet_extractor_fn(query, text)

	def _add_mappings(self, results, query):
		"""Add an element-wise mapping to each result (in place update).
		
		Args:
		    results (list): Instances of `SearchResult`
		    query (str): Query text
		
		Raises:
		    Exception: Raised when no snippet extraction function has
		    	been specified.
		"""
		get_snippet = self._snippet_extractor_fn
		if not callable(get_snippet):
			raise Exception('Searcher has invalid configuration. It is \
				configured to return mapping but any snippet \
				extraction function has not been specified, which is \
				to be used for extracting snippets used for mapping.')
		elements = utils.get_elements(query)
		for result in results:
			text = result.full_text
			result.mapping = [get_snippet(el, text) for el in elements]


class SearchFilter():

	def __init__(self):
		self._published_before = None
		self._published_after = None
		self._doctype = None

	@property
	def published_before(self):
		return self._published_before

	@published_before.setter
	def published_before(self, value):
		self._validate_date_filter(value)
		self._published_before = value

	@property
	def published_after(self):
		return self._published_after

	@published_after.setter
	def published_after(self, value):
		self._validate_date_filter(value)
		self._published_after = value

	@property
	def doctype(self):
		return self._doctype

	@doctype.setter
	def doctype(self, value):
		self._doctype = value
	
	def _validate_date_filter(self, value):
		try:
			parse_date(value)
		except:
			raise Exception('Unable to parse date filter as date')

	def apply(self, document):
		"""Check if the document satisfies all filter criteria.
		
		Args:
		    document (Document): Document to be checked
		
		Returns:
		    bool: True if all criteria are met, else False
		"""
		if self.published_after:
			date = self.published_after
			if not document.is_published_after(date):
				return False
		if self.published_before:
			date = self.published_before
			if not document.is_published_before(date):
				return False
		if self.doctype and self.doctype != 'any':
			if document.type != self.doctype:
				return False
		return True


class SearchResultsPage (list):

	def __init__(self, results):
		self._results = results
		self._search_time = None

	@property
	def results(self):
		return self._results

	@property
	def search_time(self):
		return self._search_time

	@classmethod
	def merge(self, lists_of_results):
		flat_list = [item for sublist in lists_of_results for item in sublist]
		results = [SearchResult(result[0], result[1]) for result in flat_list]
		results.sort(key=lambda x: x.score, reverse=True)
		return results

	def __str__(self):
		string = f'SearchResultsPage: {len(self._results)} results'
		string += '\n'
		string += '\n'.join([res.id for res in self._results])
		return string

	def __repr__(self):
		string = f'SearchResultsPage: {len(self._results)} results'
		string += '\n'
		string += '\n'.join([res.id for res in self._results])
		return string

	def to_json(self):
		json_obj = { 'results': [] }
		json_obj['results'] = [res.to_json() for res in self._results]
		return json_obj

class SearchResult (Document):

	def __init__(self, doc_id, score, index_id):
		super().__init__(doc_id)
		self._score = score
		self._index = index_id
		self._snippet = None
		self._mapping = None

	def __str__(self):
		return f'SearchResult: {self.id}, Score: {self.score}'

	def __repr__(self):
		return f'SearchResult: {self.id}, Score: {self.score}'

	@property
	def score (self):
		return self._score

	@property
	def snippet(self):
		return self._snippet

	@property
	def mapping(self):
		return self._mapping
	
	@snippet.setter
	def snippet(self, value):
		self._snippet = value

	@mapping.setter
	def mapping(self, value):
		self._mapping = value

	def to_json (self):
		json_obj = super().to_json()
		json_obj['score'] = self.score
		json_obj['snippet'] = self.snippet
		json_obj['mapping'] = self.mapping
		json_obj['index'] = self._index
		return json_obj

	def passes_through (self, conditions):
		return conditions.apply(self)


def _filter_family_members (results):
	results.sort(key=lambda x: x.score)
	filtrate = results[:1]
	for result in results[1:]:
		last_result = filtrate[-1]
		if result.score != last_result.score:
			filtrate.append(result)
	return filtrate


def _search_by_patent_number (pn,
								n=10,
								indexes=None,
								before=None,
								after=None,
								reranker=None):
	try:
		first_claim = db.get_first_claim(pn)
	except:
		raise Exception(f'Claim cannot be retrieved for {pn}')

	claim_text = utils.remove_claim_number(first_claim)
	return _search_by_text_query(claim_text, n, indexes, before, after)


def _search_by_text_query (query_text,
							n=10,
							indexes=None,
							before=None,
							after=None,
							reranker=None):
	if not (type(indexes) == list and len(indexes) > 0):
		print('Predicting subclasses...')
		indexes = predict_subclasses(query_text,
										N_INDEXES_TO_SEARCH,
										AVAILABLE_INDEXES)
		print('Subclasses predicted.')

	m = n
	results = []
	while len(results) < n and m <= MAX_RESULTS_LIMIT:
		results = []
		for index_id in indexes:
			for suffix in ['abs', 'ttl', 'npl']:
				index = get_index(f'{index_id}.{suffix}')
				if index is None:
					continue

				arr = index.run_text_query(query_text, m, dist=True)
				if not arr:
					continue

				arr = [(doc_id, score, index_id) for doc_id, score in arr]
				results += arr

		# Convert tuples to `SearchResult` objects
		results = [SearchResult(result[0], result[1], result[2])
							for result in results]

		# Apply date filter
		results = [result for result in results
					if result.is_published_between(before, after)]
		results = _filter_family_members(results)
		m *= 2

	results = results[:n]
	# Do re-ranking
	if reranker is not None:
		abstracts = [result.abstract for result in results]
		ranks = reranker.rank(query_text, abstracts)
		results = [results[r] for r in ranks]
	
	return results


def search (value,
			n=10,
			indexes=None,
			before=None,
			after=None,
			reranker=None):
	if utils.is_patent_number(value):
		return _search_by_patent_number(value, n, indexes, before, after, reranker)
	else:
		return _search_by_text_query(value, n, indexes, before, after, reranker)

