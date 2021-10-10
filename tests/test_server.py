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

if len(sys.argv) > 1:
	HOST = sys.argv[1]
else:
	HOST = '127.0.0.1'
print(f'Testing PQAI API on {HOST}:{PORT}')

API_TEST_TOKEN = 'test_token_asdf77bc3a9f'

import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_not_running = sock.connect_ex((HOST, PORT)) != 0
if server_not_running:
	print('Server is not running. All API tests will be skipped.')

@unittest.skipIf(server_not_running, 'Works only when true')
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

	def test_patent_data_route(self):
		url = '/patents/US7654321B2'
		response = self.api_get(url)
		self.assertSuccess(response)
		data = response.json()
		self.assertTrue('title' in data)
		self.assertTrue('abstract' in data)
		self.assertTrue('claims' in data)
		self.assertTrue('description' in data)
		self.assertTrue('publication_date' in data)

	def test_patent_title_route(self):
		url = '/patents/US7654321B2/title'
		response = self.api_get(url)
		self.assertSuccess(response)
		data = response.json()
		self.assertTrue('title' in data)
		self.assertTrue('sampling' in data['title'])

	def test_patent_abstract_route(self):
		url = '/patents/US7654321B2/abstract'
		response = self.api_get(url)
		self.assertSuccess(response)
		data = response.json()
		self.assertTrue('abstract' in data)
		self.assertTrue('formation' in data['abstract'])

	def test_patent_claims_route(self):
		url = '/patents/US7654321B2/claims'
		response = self.api_get(url)
		self.assertSuccess(response)
		data = response.json()
		self.assertTrue('claims' in data)
		self.assertEqual(len(data['claims']), 26)

	def test_patent_ind_claims_route(self):
		url = '/patents/US7654321B2/claims/independent'
		response = self.api_get(url)
		self.assertSuccess(response)
		data = response.json()
		self.assertTrue('claims' in data)
		self.assertEqual(len(data['claims']), 6)

	def test_patent_one_claims_route(self):
		url = '/patents/US7654321B2/claims/26'
		response = self.api_get(url)
		self.assertSuccess(response)
		data = response.json()
		self.assertTrue('claim' in data)
		self.assertIsInstance(data['claim'], str)
		self.assertTrue(data['claim'].startswith('26.'))

		self.assertTrue('claim_num' in data)
		self.assertIsInstance(data['claim_num'], int)
		self.assertEqual(data['claim_num'], 26)

	def test_patent_description_route(self):
		url = '/patents/US7654321B2/description'
		response = self.api_get(url)
		self.assertSuccess(response)
		data = response.json()
		self.assertTrue('description' in data)
		self.assertIsInstance(data['description'], str)

	def test_patent_citations_route(self):
		url = '/patents/US7654321B2/citations'
		response = self.api_get(url)
		self.assertSuccess(response)
		data = response.json()
		self.assertTrue('citations_backward' in data)
		self.assertIsInstance(data['citations_backward'], list)
		self.assertGreater(len(data['citations_backward']), 0)

		self.assertTrue('citations_forward' in data)
		self.assertIsInstance(data['citations_forward'], list)
		self.assertGreater(len(data['citations_forward']), 0)

	def test_patent_backward_citations_route(self):
		url = '/patents/US7654321B2/citations/backward'
		response = self.api_get(url)
		self.assertSuccess(response)
		data = response.json()
		self.assertTrue('citations_backward' in data)
		self.assertIsInstance(data['citations_backward'], list)
		self.assertGreater(len(data['citations_backward']), 0)

	def test_patent_forward_citations_route(self):
		url = '/patents/US7654321B2/citations/forward'
		response = self.api_get(url)
		self.assertSuccess(response)
		data = response.json()
		self.assertTrue('citations_forward' in data)
		self.assertIsInstance(data['citations_forward'], list)
		self.assertGreater(len(data['citations_forward']), 0)

	def test_patent_aggregated_citations_route(self):
		url = '/patents/US7654321B2/citations/aggregated?levels=3'
		response = self.api_get(url)
		self.assertSuccess(response)
		data = response.json()
		self.assertIsInstance(data, list)
		self.assertGreater(len(data), 1000)

	def test_patent_concepts_in_abstracts_route(self):
		url = '/patents/US7654321B2/abstract/concepts'
		response = self.api_get(url)
		self.assertSuccess(response)
		data = response.json()
		self.assertTrue('concepts' in data)
		self.assertIsInstance(data['concepts'], list)
		self.assertGreater(len(data['concepts']), 0)

	def test_patent_concepts_in_description_route(self):
		url = '/patents/US7654321B2/description/concepts'
		response = self.api_get(url)
		self.assertSuccess(response)
		data = response.json()
		self.assertTrue('concepts' in data)
		self.assertIsInstance(data['concepts'], list)
		self.assertGreater(len(data['concepts']), 0)

	def test_patent_cpcs_route(self):
		url = '/patents/US7654321B2/classification/cpcs'
		response = self.api_get(url)
		self.assertSuccess(response)
		data = response.json()
		self.assertTrue('cpcs' in data)
		self.assertIsInstance(data['cpcs'], list)
		self.assertGreater(len(data['cpcs']), 0)

	def test_patent_cpc_vector_route(self):
		url = '/patents/US7654321B2/vectors/cpcs'
		response = self.api_get(url)
		self.assertSuccess(response)
		data = response.json()
		self.assertTrue('vector' in data)
		self.assertIsInstance(data['vector'], list)
		self.assertGreater(len(data['vector']), 0)

	def test_patent_abstract_vector_route(self):
		url = '/patents/US7654321B2/vectors/abstract'
		response = self.api_get(url)
		self.assertSuccess(response)
		data = response.json()
		self.assertTrue('vector' in data)
		self.assertIsInstance(data['vector'], list)
		self.assertGreater(len(data['vector']), 0)

	def test_similar_concepts_route(self):
		url = '/concepts/vehicle/similar'
		response = self.api_get(url)
		self.assertSuccess(response)
		data = response.json()
		self.assertTrue('similar' in data)
		self.assertIsInstance(data['similar'], list)
		self.assertGreater(len(data['similar']), 0)

	def test_concept_vector_route(self):
		url = '/concepts/vehicle/vector'
		response = self.api_get(url)
		self.assertSuccess(response)
		data = response.json()
		self.assertTrue('vector' in data)
		self.assertIsInstance(data['vector'], list)
		self.assertGreater(len(data['vector']), 0)

	def test_drawing_route(self):
		response = self.api_get('/patents/US7654321B2/drawings/1')
		self.assertSuccess(response)

	def test_list_drawings_route(self):
		response = self.api_get('/patents/US7654321B2/drawings/')
		self.assertSuccess(response)
		self.assertEqual(8, len(response.json()['drawings']))

	def test_thumbnail_route(self):
		response = self.api_get('/patents/US7654321B2/thumbnails/1')
		self.assertSuccess(response)

	def test_list_thumbnails_route(self):
		response = self.api_get('/patents/US7654321B2/thumbnails/')
		self.assertSuccess(response)
		self.assertEqual(8, len(response.json()['thumbnails']))

	def api_get(self, route, params=None):
		url = self.endpoint + route
		if not isinstance(params, dict):
			params = dict()
		params['token'] = API_TEST_TOKEN
		response = requests.get(url, params)
		return response

	def assertSuccess(self, response):
		self.assertEqual(200, response.status_code)


if __name__ == '__main__':
	while len(sys.argv) > 1:
		sys.argv.pop()
	unittest.main()