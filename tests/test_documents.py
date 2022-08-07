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

from core.documents import Document

class TestDocument(unittest.TestCase):

    def test__check_type(self):
        doc = Document('US7654321B2')
        self.assertTrue(doc.is_patent())
        self.assertFalse(doc.is_npl())

if __name__ == '__main__':
    unittest.main()