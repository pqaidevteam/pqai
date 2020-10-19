"""
	Server must be running for these tests to pass
"""

import unittest
import requests

HOST = '127.0.0.1' 	# Server on which the PQAI server is running
PORT = 5000

# @unittest.skip('Works only when the server is running')
class TestRoutes(unittest.TestCase):

	def setUp(self):
		self.endpoint = f'http://{HOST}:{str(PORT)}'
		self.query = 'formation fluid sampling'
		self.pn = 'US7654321B2'

	def test_102_search_route_with_text_query(self):
		response = self.api_get('/documents', {'q': self.query})
		self.assertSuccess(response)
		self.assertGreater(len(response.json()['results']), 0)

	def test_102_search_route_with_patent_query(self):
		response = self.api_get('/documents', {'pn': 'US7654321B2'})
		self.assertSuccess(response)
		self.assertGreater(len(response.json()['results']), 0)

	def test_prior_art_search_route(self):
		response = self.api_get('/prior-art', {'pn': 'US7654321B2'})
		self.assertSuccess(response)
		self.assertGreater(len(response.json()['results']), 0)

	def test_103_search_route(self):
		response = self.api_get('/combinations', {'q': self.query})
		self.assertSuccess(response)
		self.assertGreater(len(response.json()['results']), 0)

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
		response = requests.get(url, params)
		return response

	def assertSuccess(self, response):
		self.assertEqual(200, response.status_code)


if __name__ == '__main__':
	unittest.main()