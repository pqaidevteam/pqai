import unittest

import sys
from pathlib import Path
test_dir = str(Path(__file__).parent.resolve())
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR.resolve()))

from core.obvious import Combiner

class TestCombiner(unittest.TestCase):

	def setUp(self):
		self.query = "base and station"
		self.docs = [
			"base level",
			"mobile stations",
			"station"
		]

	def test_combination_suggestions(self):
		combiner = Combiner(self.query, self.docs)
		combinations = combiner.get_combinations(1)
		expected = set(['base level', 'station'])
		self.assertEqual(expected, combinations)

if __name__ == '__main__':
    unittest.main()