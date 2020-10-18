import unittest

import sys
from pathlib import Path
TEST_DIR = str(Path(__file__).parent.resolve())
BASE_DIR = str(Path(__file__).parent.parent.resolve())
sys.path.append(BASE_DIR)

from core.datasets import Dataset, PoC

class TestDatasetClass(unittest.TestCase):

	def setUp(self):
		self.sample_a = { 'feature': 'frog', 'label': 'amphibian' }
		self.sample_b = { 'feature': 'crow', 'label': 'bird'}
		self.samples = [self.sample_a, self.sample_b]
		self.dataset = Dataset(self.samples)

	def test_can_get_a_sample(self):
		sample = self.dataset[0]
		self.assertEqual(self.sample_a, sample)

	def test_can_tell_size(self):
		self.assertEqual(2, len(self.dataset))

class TestPoCDatasetClass(unittest.TestCase):

	@classmethod
	def setUpClass(self):
		self.dataset = PoC()

	def test_can_get_a_sample(self):
		sample = self.dataset[0]
		self.assertIsInstance(sample, dict)

	def test_can_tell_size(self):
		self.assertGreater(len(self.dataset), 90000)

if __name__ == '__main__':
    unittest.main()