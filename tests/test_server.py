"""
	Server must be running for these tests to pass
"""

import unittest
import requests

import sys
from pathlib import Path
TEST_DIR = str(Path(__file__).parent.resolve())
BASE_DIR = str(Path(__file__).parent.parent.resolve())
sys.path.append(BASE_DIR)

from config.config import port as PORT
HOST = '127.0.0.1' 	# Server on which the PQAI server is running
API_TEST_TOKEN = 'test_token_asdf77bc3a9f'

# @unittest.skip('Works only when the server is running')
class TestRoutes(unittest.TestCase):

	def setUp(self):
		self.endpoint = f'http://{HOST}:{str(PORT)}'
		self.query = 'formation fluid sampling'
		self.pn = 'US7654321B2'

	def test_102_search_route_with_text_query(self):
		response = self.api_get('/search/102', {'q': self.query})
		self.assertSuccess(response)
		self.assertGreater(len(response.json()['results']), 0)

	def test_patent_prior_art_search_route(self):
		response = self.api_get('/prior-art/patent', {'pn': 'US7654321B2'})
		self.assertSuccess(response)
		self.assertGreater(len(response.json()['results']), 0)

	def test_similar_patent_search_route(self):
		response = self.api_get('/similar', {'pn': 'US7654321B2'})
		self.assertSuccess(response)
		self.assertGreater(len(response.json()['results']), 0)

	def test_103_search_route(self):
		response = self.api_get('/search/103', {'q': self.query})
		self.assertSuccess(response)
		self.assertGreater(len(response.json()['results']), 0)

	def test_document_retrieval_route(self):
		response = self.api_get('/documents', {'id': 'US7654321B2'})
		self.assertSuccess(response)
		self.assertIsInstance(response.json(), dict)

	def test_snippets_route(self):
		response = self.api_get('/snippets', {'q': self.query, 'pn': self.pn})
		self.assertSuccess(response)

	def test_mappings_route(self):
		response = self.api_get('/mappings', {'q': self.query, 'pn': self.pn})
		self.assertSuccess(response)

	def test_datasets_route(self):
		response = self.api_get('/datasets', { 'dataset': 'poc', 'n': 23 })
		self.assertSuccess(response)
		self.assertTrue('anc' in response.json())

	def api_get(self, route, params):
		url = self.endpoint + route
		params['token'] = API_TEST_TOKEN
		response = requests.get(url, params)
		return response

	def assertSuccess(self, response):
		self.assertEqual(200, response.status_code)


if __name__ == '__main__':
	unittest.main()