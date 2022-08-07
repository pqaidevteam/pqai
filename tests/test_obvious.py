import unittest

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
		expected = set([0, 2])
		self.assertEqual(expected, combinations)

if __name__ == '__main__':
    unittest.main()