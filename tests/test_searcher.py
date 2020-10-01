import unittest

import sys
from pathlib import Path
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR.resolve()))

from core.searcher import Searcher, SearchFilter, SearchResultsPage, SearchResult
from core.indexes import get_index, Index
from core.documents import Document


class TestSearcherClass(unittest.TestCase):
	
	def setUp(self):
		self.searcher = Searcher()
		self.indexes = ['H04W.ttl', 'H04W.npl']
		self.query = 'wireless communication with base station'

	def test_result_count_initialization(self):
		self.assertIsInstance(self.searcher.result_count, int)

	def test_can_set_result_count(self):
		self.searcher.result_count = 22
		self.assertEqual(22, self.searcher.result_count)

	def test_return_snippet_initalization(self):
		self.assertIsInstance(self.searcher.return_snippets, bool)

	def test_can_set_snippet_preference(self):
		self.searcher.return_snippets = True
		self.assertTrue(self.searcher.return_snippets)

	def test_return_mappings_initialization(self):
		self.assertIsInstance(self.searcher.return_mappings, bool)

	def test_can_set_mapping_preference(self):
		self.searcher.return_mappings = True
		self.assertTrue(self.searcher.return_mappings)

	def test_search_with_preamble_initalization(self):
		self.assertIsInstance(self.searcher.search_with_preamble, bool)

	def test_can_set_preamble_search(self):
		self.searcher.search_with_preamble = True
		self.assertTrue(self.searcher.search_with_preamble)

	def test_can_specify_filter(self):
		filter = SearchFilter()
		self.searcher.filter = filter
		self.assertIsInstance(self.searcher.filter, SearchFilter)

	def test_can_set_indexes_to_search(self):
		self.searcher.indexes = self.indexes
		self.assertIsInstance(self.searcher.indexes[0], Index)

	def test_try_search_without_specifying_indexes(self):
		def search_without_indexes():
			self.searcher.run(self.query)
		self.assertRaises(Exception, search_without_indexes)

	def test_can_set_reranker(self):
		def dummy_reranker_fn(results):
			results.reverse()
			return results
		self.searcher.reranker = dummy_reranker_fn
		self.assertIs(dummy_reranker_fn, self.searcher.reranker)

	def test_result_count_with_text_query(self):
		self.searcher.indexes = self.indexes
		self.searcher.result_count = 15
		results = self.searcher.run(self.query)
		self.assertEqual(15, len(results))

	def test_exclusive_npl_search(self):
		self.searcher.filter = SearchFilter()
		self.searcher.filter.doctype = 'npl'
		self.searcher.indexes = ['H04W.ttl', 'H04W.npl']
		results = self.searcher.run(self.query)
		self.assertTrue(bool(results) and all([res.is_npl() for res in results]))

	def test_exclusive_patent_search(self):
		self.searcher.filter = SearchFilter()
		self.searcher.filter.doctype = 'patent'
		self.searcher.indexes = self.indexes
		results = self.searcher.run(self.query)
		self.assertTrue(bool(results) and all([res.is_patent() for res in results]))

	def test_search_with_cutoff_dates(self):
		d0 = '2009-12-12'
		d1 = '2015-01-01'
		self.searcher.filter = SearchFilter()
		self.searcher.filter.published_after = d0
		self.searcher.filter.published_before = d1
		self.searcher.indexes = self.indexes
		results = self.searcher.run(self.query)
		self.assertTrue(bool(results) and all([res.is_published_between(d0, d1) for res in results]))

	def test_search_with_invalid_snippet_configuration(self):
		self.searcher.return_snippets = True
		self.searcher.snippet_extractor = None # Invalid
		self.searcher.indexes = self.indexes
		def run_search():
			return self.searcher.run(self.query)
		self.assertRaises(Exception, run_search)

	def test_search_with_invalid_mapping_configuration(self):
		self.searcher.return_mappings = True
		self.searcher.snippet_extractor = None # Invalid
		self.searcher.indexes = self.indexes
		def run_search():
			return self.searcher.run(self.query)
		self.assertRaises(Exception, run_search)

	def test_return_snippets(self):
		def dummy_snippet_extractor(query, text):
			return 'Test snippet'
		self.searcher.return_snippets = True
		self.searcher.snippet_extractor = dummy_snippet_extractor
		self.searcher.indexes = self.indexes
		results = self.searcher.run(self.query)
		self.assertTrue(bool(results) and all([bool(res.snippet) for res in results]))

	def test_return_mappings(self):
		def dummy_snippet_extractor(query, text):
			return 'Test snippet'
		self.searcher.return_mappings = True
		self.searcher.snippet_extractor = dummy_snippet_extractor
		self.searcher.indexes = self.indexes
		results = self.searcher.run(self.query)
		self.assertTrue(bool(results) and all([bool(res.mapping) for res in results]))

class TestSearchFilterClass(unittest.TestCase):
	
	def setUp(self):
		self.filter = SearchFilter()

	def test_set_published_before_filter(self):
		self.filter.published_before = '2016-01-28'
		self.assertEqual('2016-01-28', self.filter.published_before)

	def test_invalid_published_before_filter(self):
		def set_invalid_date():
			self.filter.published_before = '202-23-3'
		self.assertRaises(Exception, set_invalid_date)

	def test_set_published_after_filter(self):
		self.filter.published_after = '2002-02-16'
		self.assertEqual('2002-02-16', self.filter.published_after)

	def test_invalid_published_after_filter(self):
		def set_invalid_date():
			self.filter.published_after = '202-23-3'
		self.assertRaises(Exception, set_invalid_date)

	def test_apply_date_filter(self):
		doc = Document('US7654321B2')
		self.filter.published_after = '2009-01-01'
		self.filter.published_before = '2009-12-31'
		a = self.filter.apply(doc)
		self.filter.published_after = '2010-01-01'
		self.filter.published_before = '2010-12-31'
		b = self.filter.apply(doc)
		expected = (False, True)
		actual = (a, b)
		self.assertEqual(expected, actual)


class TestSearchResultsPage(unittest.TestCase):

	def setUp(self):
		results = []
		self.searchresults = SearchResultsPage(results)


class TestSearchResultClass(unittest.TestCase):

	def setUp(self):
		self.search_result = SearchResult('US7654321B2', 0.234)

	def test_passes_through_before_date_filter_true(self):
		filter_criteria = SearchFilter()
		filter_criteria.published_before = '2012-02-20'
		self.assertTrue(self.search_result.passes_through(filter_criteria))

	def test_passes_through_before_date_filter_false(self):
		filter_criteria = SearchFilter()
		filter_criteria.published_before = '1998-02-20'
		self.assertFalse(self.search_result.passes_through(filter_criteria))

	def test_passes_through_after_date_filter_true(self):
		filter_criteria = SearchFilter()
		filter_criteria.published_after = '1998-02-20'
		self.assertTrue(self.search_result.passes_through(filter_criteria))

	def test_passes_through_after_date_filter_false(self):
		filter_criteria = SearchFilter()
		filter_criteria.published_after = '2012-02-20'
		self.assertFalse(self.search_result.passes_through(filter_criteria))

	def test_passes_through_doc_type(self):
		filter_criteria = SearchFilter()
		filter_criteria.doctype = 'npl'
		a = self.search_result.passes_through(filter_criteria)
		filter_criteria.doctype = 'patent'
		b = self.search_result.passes_through(filter_criteria)
		filter_criteria.doctype = 'any'
		c = self.search_result.passes_through(filter_criteria)
		expected = (False, True, True)
		actual = (a, b, c)
		self.assertEqual(expected, actual)

if __name__ == '__main__':
    unittest.main()