import unittest

import sys
from pathlib import Path
TEST_DIR = str(Path(__file__).parent.resolve())
BASE_DIR = str(Path(__file__).parent.parent.resolve())
sys.path.append(BASE_DIR)

from core.snippet import SnippetExtractor
from core.documents import Document

class TestSnippetExtractor(unittest.TestCase):

	def setUp(self):
		self.query = 'fluid formation sampling'
		self.longquery = 'A method of sampling formation fluids. The method includes lowering a sampling apparatus into a borewell.'
		self.doc = Document('US7654321B2')
		self.text = self.doc.full_text

	def test_can_create_snippet(self):
		snip = SnippetExtractor.extract_snippet(self.query, self.text)
		self.assertIsInstance(snip, str)
		self.assertGreater(len(snip), 10)

	def test_can_do_mapping(self):
		mapping = SnippetExtractor.map(self.longquery, self.text)
		self.assertIsInstance(mapping, list)
		self.assertGreater(len(mapping), 1)


if __name__ == '__main__':
	unittest.main()