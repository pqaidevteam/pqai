import numpy as np

from core.indexes import VectorIndex
from core.results import SearchResult
import itertools

class Searcher():

	_invalid_needle_msg = "Invalid needle"
	_invalid_haystack_msg = "Invalid haystack"
	_no_haystack_msg = "No haystacks available for search"

	def __init__(self):
		self._compat_haystack = None
		self._needle_compatibility_fn = None
		self._haystack_compatibility_fn = _is_compatible_haystack
		self._search_fn = None
		self._sort_fn = lambda x: x

	def search(self, needle, haystack, n_results=10):
		self._check_needle_compatibility(needle)
		self._check_haystack_compatibility(haystack)
		haystack = [haystack] if self._is_one_haystack(haystack) else haystack
		n_results = max(0, n_results)
		return self._results_from_many(needle, haystack, n_results)

	def _check_needle_compatibility(self, needle):
		if not self._needle_compatibility_fn(needle):
			raise Exception(self._invalid_needle_msg)

	def _check_haystack_compatibility(self, haystack):
		if isinstance(haystack, self._compat_haystack):
			return None
		elif isinstance(haystack, list) or isinstance(haystack, set):
			if all([isinstance(item, self._compat_haystack) for item in haystack]):
				return None
		else:
			raise Exception(self._invalid_haystack_msg)

	def _is_one_haystack(self, haystack):
		if isinstance(haystack, self._compat_haystack):
			return True
		if isinstance(haystack, list) or isinstance(haystack, set):
			return False

	def _results_from_one(self, needle, haystack, n):
		return self._search_fn(needle, haystack, n)
	
	def _results_from_many(self, needle, haystack, n):
		list_of_lists = [self._results_from_one(needle, hs, n) for hs in haystack]
		results = self._flatten(list_of_lists)
		results = self._sort_fn(results)
		results = self._deduplicate(results)
		return results[:n]

	def _flatten(self, list2d):
		return list(itertools.chain.from_iterable(list2d))

	def _deduplicate(self, results):
		first_result = results[0]
		arr = [first_result]
		already_added = set([first_result.id])
		for this in results:
			last = arr[-1]
			if this.score == last.score or this.id in already_added:
				continue
			else:
				arr.append(this)
				already_added.add(this.id)
		return arr


class VectorIndexSearcher(Searcher):

	_invalid_needle_msg = "Expected a vector as query"
	_invalid_haystack_msg = "Can only search VectorIndex objects"
	_no_haystack_msg = "No VectorIndex objects provided for search"

	def __init__(self):
		self._compat_haystack = VectorIndex
		self._needle_compatibility_fn = self._is_vector
		self._search_fn = self._run_vector_query
		self._sort_fn = self._sort_results

	def _is_vector(self, item):
		try:
			vector = np.array(item, dtype='float32')
		except:
			return False
		finally:
			return True

	def _run_vector_query(self, vector, index, n):
		pairs = index.search(vector, n)
		index_id = index.name
		triplets = [(res_id, index_id, score) for res_id, score in pairs]
		results = [SearchResult(*triplet) for triplet in triplets]
		return results

	def _sort_results(self, results):
		score = lambda x: x.score
		return sorted(results, key=score)