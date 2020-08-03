from core import utils
from core import db
from core.indexes import index_ids as AVAILABLE_INDEXES
from core.indexes import get_index
from core.documents import Document
from core.classifiers import BOWSubclassPredictor

predict_subclasses = BOWSubclassPredictor().predict_subclasses

N_INDEXES_TO_SEARCH = 3
MAX_RESULTS_LIMIT = 200

class SearchResult (Document):

	def __init__(self, doc_id, score):
		super().__init__(doc_id)
		self._score = score
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
		return json_obj


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
			for suffix in ['abs', 'ttl']:
				index = get_index(f'{index_id}.{suffix}')
				if index is None:
					continue

				arr = index.run_text_query(query_text, m, dist=True)
				if not arr:
					continue

				results += arr

		# Convert tuples to `SearchResult` objects
		results = [SearchResult(result[0], result[1])
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

