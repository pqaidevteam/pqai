import unittest
import numpy as np

import sys
from pathlib import Path
TEST_DIR = str(Path(__file__).parent.resolve())
BASE_DIR = str(Path(__file__).parent.parent.resolve())
sys.path.append(BASE_DIR)

from core.search import Searcher, VectorIndexSearcher
from core.indexes import IndexesDirectory
from config.config import indexes_dir


class TestSearcherClass(unittest.TestCase):
	pass


class TestVectorIndexSearcher(unittest.TestCase):

	def setUp(self):
		self.indexes = IndexesDirectory(indexes_dir)
		self.searcher = VectorIndexSearcher()
		self.unitvec = np.ones(self.indexes.dims)

	def test_can_search_in_one_index(self):
		results = self.search(self.unitvec, 'H04W.ttl', 10)
		self.assertGreaterEqual(len(results), 10)

	def test_can_search_in_multiple_indexes(self):
		results = self.search(self.unitvec, 'H04W', 10)
		self.assertGreaterEqual(len(results), 10)

	def test_ask_for_zero_results(self):
		results = self.search(self.unitvec, 'H04W', 0)
		self.assertCount(0, results)

	def test_ask_for_negative_results(self):
		results = self.search(self.unitvec, 'H04W', -1)
		self.assertCount(0, results)

	def search(self, needle, haystack, n):
		indexes = self.indexes.get(haystack)
		results = self.searcher.search(needle, indexes, n)
		return results

	def assertCount(self, n, results):
		self.assertIsInstance(results, list)
		self.assertEqual(n, len(results))

if __name__ == '__main__':
    unittest.main()