import unittest

import sys
from pathlib import Path
TEST_DIR = str(Path(__file__).parent.resolve())
BASE_DIR = str(Path(__file__).parent.parent.resolve())
sys.path.append(BASE_DIR)

from core.index_selection import SublassesBasedIndexSelector
from core.indexes import IndexesDirectory
from config.config import indexes_dir

class TestSubclassIndexSelector(unittest.TestCase):

	def setUp(self):
		indexes = IndexesDirectory(indexes_dir) 
		self.index_selector = SublassesBasedIndexSelector(indexes)

	def test_selects_indexes_accurately(self):
		query = 'cellular networks'
		indexes = self.index_selector.select(query, 5)
		self.assertIsInstance(indexes, list)


if __name__ == '__main__':
    unittest.main()