import unittest

import sys
from pathlib import Path
BASE_DIR = str(Path(__file__).parent.parent.parent.resolve())
sys.path.append(BASE_DIR)

from api import SuggestCPCs, PredictGAUs, SuggestSynonyms, ExtractConcepts
from api import DefineCPC


class TestSuggestCPCsRequest(unittest.TestCase):

    def test_valid_output(self):
        cpcs = SuggestCPCs({'text': 'electric vehicles'}).serve()
        self.assertIsInstance(cpcs, list)
        self.assertGreater(len(cpcs), 0)


class TestExtractConceptRequest(unittest.TestCase):

    def setUp(self):
        self.text = "An addressing scheme for non-volatile memory arrays having short circuit defects that manages the demand for error correction."

    def test_valid_output(self):
        concepts = ExtractConcepts({'text': self.text}).serve()
        self.assertIsInstance(concepts, list)
        self.assertGreater(len(concepts), 0)

class TestPredictGAUsRequest(unittest.TestCase):

    def setUp(self):
        self.text = "An addressing scheme for non-volatile memory arrays having short circuit defects that manages the demand for error correction."

    def test_valid_output(self):
        gaus = PredictGAUs({'text': self.text}).serve()
        self.assertIsInstance(gaus, list)
        self.assertGreater(len(gaus), 0)

class TestSuggestSynonymsRequest(unittest.TestCase):

    def setUp(self):
        self.text = "electric vehicle"

    def test_valid_output(self):
        synonyms = SuggestSynonyms({'text': self.text}).serve()
        self.assertIsInstance(synonyms, list)
        self.assertGreater(len(synonyms), 0)


class TestDefineCPCRequest(unittest.TestCase):
    
    def test_normal_operation(self):
        cpc = 'H04W52/02'
        definition = DefineCPC({'cpc': cpc}).serve()
        self.assertIsInstance(definition, list)
        self.assertEqual(5, len(definition))

    def test_get_short_form_definitions(self):
        cpc = 'H04W52/02'
        definition = DefineCPC({'cpc': cpc, 'short': '1'}).serve()
        self.assertIsInstance(definition, str)

if __name__ == '__main__':
    unittest.main()