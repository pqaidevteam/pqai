import unittest

import sys
from pathlib import Path
TEST_DIR = str(Path(__file__).parent.resolve())
BASE_DIR = str(Path(__file__).parent.parent.resolve())
sys.path.append(BASE_DIR)

import numpy as np
from core.indexes import Index, IndexesDirectory
from core.indexes import AnnoyIndexReader, AnnoyIndex
from core.query import VectorQuery


class TestAnnoyIndexReaderClass(unittest.TestCase):

	def test_read_from_json_ann_files(self):
		ann_file = f'{TEST_DIR}/test_Y04S.ttl.ann'
		json_file = f'{TEST_DIR}/test_Y04S.ttl.items.json'
		reader = AnnoyIndexReader(768, 'angular')
		index = reader.read_from_ann_json(ann_file, json_file)
		self.assertIsInstance(index, AnnoyIndex)


class TestAnnoyIndexClass(unittest.TestCase):

	def setUp(self):
		ann_file = f'{TEST_DIR}/test_Y04S.ttl.ann'
		json_file = f'{TEST_DIR}/test_Y04S.ttl.items.json'
		reader = AnnoyIndexReader(768, 'angular')
		self.index = reader.read_from_ann_json(ann_file, json_file)

	def test_run_query(self):
		vector = np.ones(768)
		query = VectorQuery(vector)
		n_results = 10
		results = query.run(self.index, n_results)
		self.assertIsInstance(results, list)
		self.assertEqual(n_results, len(results))


class TestIndexesDirectory(unittest.TestCase):

	def setUp(self):
		path = f'{BASE_DIR}/indexes'
		self.indexes = IndexesDirectory(path)

	def test_can_get_indexes(self):
		indexes = self.get_index('H04W')
		are_index_objects = [isinstance(idx, AnnoyIndex) for idx in indexes]
		self.assertTrue(all(are_index_objects))
		self.assertEqual(3, len(indexes))

	def test_return_empty_for_inexistent_index(self):
		indexes = self.get_index('Z007')
		self.assertEqual([], indexes)

	def test_available_indexes(self):
		index_ids = self.indexes.available()
		self.assertIsInstance(index_ids, set)
		self.assertGreater(len(index_ids), 0)

	def get_index(self, index_code):
		index = self.indexes.get(index_code)
		return index


if __name__ == '__main__':
    unittest.main()