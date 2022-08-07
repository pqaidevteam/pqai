import unittest
import numpy as np

import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ['TEST'] = "1"

from pathlib import Path
TEST_DIR = str(Path(__file__).parent.resolve())
BASE_DIR = str(Path(__file__).parent.parent.resolve())
ENV_PATH = "{}/.env".format(BASE_DIR)

from dotenv import load_dotenv
load_dotenv(ENV_PATH)

import sys
sys.path.append(BASE_DIR)

from core.indexes import Index, IndexesDirectory
from core.indexes import AnnoyIndexReader, AnnoyIndex
from core.indexes import FaissIndexReader, FaissIndex
from core.query import VectorQuery
from config.config import indexes_dir


class TestAnnoyIndexReaderClass(unittest.TestCase):

	def test_read_from_json_ann_files(self):
		ann_file = f'{indexes_dir}Y02T.ttl.ann'
		json_file = f'{indexes_dir}Y02T.ttl.items.json'
		reader = AnnoyIndexReader(768, 'angular')
		index = reader.read_from_files(ann_file, json_file)
		self.assertIsInstance(index, AnnoyIndex)


class TestAnnoyIndexClass(unittest.TestCase):

	def setUp(self):
		ann_file = f'{indexes_dir}/Y02T.ttl.ann'
		json_file = f'{indexes_dir}/Y02T.ttl.items.json'
		reader = AnnoyIndexReader(768, 'angular')
		self.index = reader.read_from_files(ann_file, json_file)

	def test_run_query(self):
		vector = np.ones(768)
		query = VectorQuery(vector)
		n_results = 10
		results = query.run(self.index, n_results)
		self.assertIsInstance(results, list)
		self.assertEqual(n_results, len(results))


class TestFaissIndexReaderClass(unittest.TestCase):

	def test_read_from_files(self):
		index_file = f'{indexes_dir}/B68G.abs.faiss'
		json_file = f'{indexes_dir}/B68G.abs.items.json'
		r = FaissIndexReader()
		index = r.read_from_files(index_file, json_file)
		self.assertIsInstance(index, FaissIndex)


class TestFaissIndexClass(unittest.TestCase):

	def setUp(self):
		index_file = f'{indexes_dir}/B68G.abs.faiss'
		json_file = f'{indexes_dir}/B68G.abs.items.json'
		r = FaissIndexReader()
		self.index = r.read_from_files(index_file, json_file)

	def test_run_query(self):
		vector = np.ones(768)
		query = VectorQuery(vector)
		n_results = 10
		results = query.run(self.index, n_results)
		self.assertIsInstance(results, list)
		self.assertEqual(n_results, len(results))


class TestIndexesDirectory(unittest.TestCase):

	def setUp(self):
		self.indexes = IndexesDirectory(indexes_dir)

	def test_can_get_annoy_indexes(self):
		indexes = self.get_index('Y02T')
		are_index_objects = [isinstance(idx, AnnoyIndex) for idx in indexes]
		self.assertTrue(all(are_index_objects))
		self.assertEqual(3, len(indexes))

	def test_can_get_faiss_indexes(self):
		indexes = self.get_index('B68G')
		are_index_objects = [isinstance(idx, FaissIndex) for idx in indexes]
		self.assertTrue(all(are_index_objects))
		self.assertEqual(1, len(indexes))

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