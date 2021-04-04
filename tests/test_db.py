import unittest

# Run tests without using GPU
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
os.environ['TEST'] = "1"

import sys
from pathlib import Path
TEST_DIR = str(Path(__file__).parent.resolve())
BASE_DIR = str(Path(__file__).parent.parent.resolve())
sys.path.append(BASE_DIR)

from core import db

class TestDBModule(unittest.TestCase):

    def test_can_fetch_patent_bibliography(self):
        bib = db.get_bibliography('US7654321B2')
        self.assertIsInstance(bib, dict)
        self.assertIsInstance(bib['title'], str)
        self.assertIsInstance(bib['abstract'], str)
        self.assertIsInstance(bib['assignees'], list)
        self.assertFalse('description' in bib)

    def test_can_fetch_patent_data_full(self):
        data = db.get_patent_data('US7654321B2')
        self.assertIsInstance(data['title'], str)
        self.assertIsInstance(data['abstract'], str)
        self.assertIsInstance(data['description'], str)
        self.assertIsInstance(data['assignees'], list)

    def test_get_full_text(self):
        full_text = db.get_full_text('US7654321B2')
        self.assertIsInstance(full_text, str)

    def test_get_cpcs(self):
        cpcs = db.get_cpcs('US7654321B2')
        self.assertIsInstance(cpcs, list)
        self.assertGreater(len(cpcs), 0)

    def test_get_claims(self):
        claims = db.get_claims('US7654321B2')
        self.assertIsInstance(claims, list)
        self.assertGreater(len(claims), 0)
        self.assertIsInstance(claims[0], str)

    def test_get_first_claim(self):
        clm = db.get_first_claim('US7654321B2')
        self.assertIsInstance(clm, str)


if __name__ == '__main__':
    unittest.main()
