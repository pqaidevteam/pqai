import unittest

import sys
from pathlib import Path
TEST_DIR = str(Path(__file__).parent.resolve())
BASE_DIR = str(Path(__file__).parent.parent.resolve())
sys.path.append(BASE_DIR)

from core.api import APIRequest, SearchRequest102, SearchRequest103
from core.api import SnippetRequest, MappingRequest
from core.api import BadRequestError, ServerError
from core.filters import PublicationDateFilter
from dateutil.parser import parse as parse_date


class TestRequestClass(unittest.TestCase):

	class GreetingRequest(APIRequest):

		greetings = { 'en': 'Hello', 'de': 'Hallo' }

		def __init__(self, req_data):
			super().__init__(req_data)

		def _serving_fn(self):
			lang = self._data['lang']
			return self.greetings[lang]

		def _validation_fn(self):
			return 'lang' in self._data

	def test_can_create_dummy_request(self):
		req = APIRequest()
		self.assertEqual(req.serve(), None)

	def test_serving_fn_operation(self):
		req = self.GreetingRequest({ 'lang': 'en' })
		self.assertEqual('Hello', req.serve())

	def test_raises_error_on_invalid_request(self):
		req = self.GreetingRequest({ 'locale': 'en' })
		self.assertRaises(BadRequestError, req.serve)

	def test_raises_error_on_expection_during_serving(self):
		req = self.GreetingRequest({ 'lang': 'hi' })
		self.assertRaises(ServerError, req.serve)


class TestSearchRequest102Class(unittest.TestCase):

	def setUp(self):
		self.query = 'fire fighting drones'
		self.date = '2012-12-12'
		self.subclass = 'A62C'
		self.latent_query = 'drone uses dry ice canisters'

	def test_simple_search_request(self):
		results = self.search({ 'q': self.query })
		self.assertGreater(len(results), 0)

	def test_return_custom_number_of_results(self):
		results = self.search({ 'q': self.query, 'n': 13 })
		self.assertEqual(13, len(results))

	def test_query_with_before_cutoff_date(self):
		results = self.search({ 'q': self.query, 'before': self.date })
		def published_before(r):
			d1 = parse_date(r['publication_date'])
			d2 = parse_date(self.date)
			return d1 <= d2
		self.assertForEach(results, published_before)

	def test_query_with_after_cutoff_date(self):
		results = self.search({ 'q': self.query, 'after': self.date})
		def published_after(r):
			d1 = parse_date(r['publication_date'])
			d2 = parse_date(self.date)
			return d1 >= d2
		self.assertForEach(results, published_after)

	def test_query_with_index_specified(self):
		cc = self.subclass
		results = self.search({ 'q': self.query, 'idx': cc })
		from_cc = lambda r: r['index'].startswith(cc)
		self.assertForEach(results, from_cc)

	def test_latent_query_affects_results(self):
		latent = self.search({ 'q': self.query, 'lq': self.latent_query })
		without = self.search({ 'q': self.query })
		self.assertNotEqual(latent, without)

	def test_return_only_non_patent_results(self):
		results = self.search({ 'q': self.query, 'type': 'npl' })
		is_npl = lambda r: r['index'].endswith('npl')
		self.assertForEach(results, is_npl)

	def test_include_snippets(self):
		results = self.search({ 'q': self.query, 'snip': 1 })
		has_snippet = lambda r: r['snippet']
		self.assertForEach(results, has_snippet)

	def test_include_mappings(self):
		results = self.search({ 'q': self.query, 'maps': 1 })
		has_mappings = lambda r: r['mapping']
		self.assertForEach(results, has_mappings)

	def test_raises_error_with_bad_request(self):
		bad_req = lambda: self.search({ 'qry': self.query })
		self.assertRaises(BadRequestError, bad_req)

	def search(self, req):
		req = SearchRequest102(req)
		results = req.serve()['results']
		return results

	def assertForEach(self, results, condition):
		truth_arr = [condition(res) for res in results]
		self.assertTrue(all(truth_arr))
		

class TestSearchRequest103Class(unittest.TestCase):

	def setUp(self):
		self.query = 'fire fighting drone uses dry ice'

	def test_simple_search(self):
		combinations = self.search({ 'q': self.query })
		self.assertGreater(len(combinations), 0)

	def test_return_custom_number_of_results(self):
		combinations = self.search({ 'q': self.query, 'n': 8 })
		self.assertEqual(8, len(combinations))

	def search(self, req):
		req = SearchRequest103(req)
		results = req.serve()['results']
		return results

if __name__ == '__main__':
    unittest.main()