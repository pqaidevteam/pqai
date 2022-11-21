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

from core.sensible_span_extractor import SensibleSpanExtractor, SubsequenceExtractor


class TestSensibleSpanExtractor(unittest.TestCase):

	def setUp(self):
		self.extractor = SensibleSpanExtractor()

	def test_generates_span_1(self):
		sent = 'The present invention relates to an epitaxial group-III-nitride buffer layer structure on a heterosubstrate.'
		span = 'group-III-nitride buffer layer structure'
		self.assertSpan(sent, span)

	def test_generates_span_2(self):
		sent = 'Another object of the present invention is to provide a fire fighting drone.'
		span = 'a fire fighting drone.'
		self.assertSpan(sent, span)

	def test_return_ranked_1(self):
		sent = 'Another) object of the present invention is to provide a fire fighting drone.'
		span = 'a fire fighting drone.'
		res = self.extractor.return_ranked(sent)
		self.assertEqual(res[0], span)

	def test_return_ranked_2(self):
		sent = 'Another (object of the present invention is to provide a fire fighting drone.'
		span = 'a fire fighting drone.'
		res = self.extractor.return_ranked(sent)
		self.assertEqual(res[0], span)

	def assertSpan(self, sent, span):
		self.assertEqual(span, self.extractor.extract_from(sent))


class TestSubsequenceExtractor(unittest.TestCase):

	def setUp(self):
		self.extractor = SubsequenceExtractor([0, 1, 2, 3])

	def test_subsequences_of_zero_length(self):
		subseqs = self.extractor.extract(0)
		self.assertEqual(0, len(subseqs))

	def test_subsequences_of_unit_length(self):
		subseqs = self.extractor.extract(1)
		self.assertEqual(4, len(subseqs))

	def test_subsequences_between_lengths(self):
		subseqs = self.extractor.extract(2, 3)
		self.assertEqual(5, len(subseqs))


if __name__ == '__main__':
	unittest.main()
