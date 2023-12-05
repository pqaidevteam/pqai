import unittest
from tqdm import tqdm

import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ['TEST'] = "1"

from pathlib import Path
TEST_DIR = str(Path(__file__).parent.resolve())
BASE_DIR = str(Path(__file__).parent.parent.resolve())
ENV_PATH = "{}/.env".format(BASE_DIR)

from dotenv import load_dotenv
load_dotenv(ENV_PATH)

import sys
sys.path.append(BASE_DIR)

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch

from core.snippet import SnippetExtractor, CombinationalMapping
from core.documents import Document, Patent
from core.reranking import CustomRanker, ConceptMatchRanker
ranker = ConceptMatchRanker()

class TestSnippetExtractor(unittest.TestCase):

    def setUp(self):
        self.query = 'fluid formation sampling'
        self.longquery = 'A method of sampling formation fluids. The method includes lowering a sampling apparatus into a borewell.'
        self.doc = Document('US7654321B2')
        self.text = self.doc.full_text

    def test__can_add_few_words_before_snippet(self):
        snip = SnippetExtractor.extract_snippet(self.query, self.text)
        self.assertIsInstance(snip, str)
        self.assertGreater(len(snip), 10)

    def test__can_add_few_words_after_snippet(self):
        self.query1 = 'fluid formation sampling'
        self.text1 = 'I am mayank rakesh and I live with my parents in dehradun with three dogs and one cat. A fluid sampling system retrieves a formation fluid sample from a formation surrounding a wellbore extending along a wellbore axis, wherein the formation has a virgin fluid and a contaminated fluid therein. At least one cleanup flowline is fluidly connected to the first and second guard inlets for passing contaminated fluid, and an evaluation flowline is fluidly connected to the sample inlet for collecting virgin fluid.'
        snip = SnippetExtractor.extract_snippet(self.query1, self.text1)
        self.assertIsInstance(snip, str)
        self.assertGreater(len(snip), 10)

    def test__can_do_mapping(self):
        mapping = SnippetExtractor.map(self.longquery, self.text)
        self.assertIsInstance(mapping, list)
        self.assertGreater(len(mapping), 1)


class CombinationalMappingClass(unittest.TestCase):

    def setUp(self):
        self.el1 = 'A fire fighting drone for fighting forest fires.'
        self.el2 =  'The done uses dry ice to extinguish the fire.'
        self.query = self.el1 + ' ' + self.el2
        self.text1 = Patent('US20010025712A1').full_text # drone patent
        self.text2 = Patent('US20170087393A1').full_text # dry ice patent

    def test_mapping_operation(self):
        texts = [self.text1, self.text2]
        mapping = CombinationalMapping(self.query, texts).map()
        self.assertIsInstance(mapping, list)
        self.assertEqual(2, len(mapping))
        self.assertTrue(all([isinstance(m, dict) for m in mapping]))
        self.assertNotEqual(mapping[0]['doc'], mapping[1]['doc'])

    def test_can_create_mapping_table(self):
        texts = [self.text1, self.text2]
        table = CombinationalMapping(self.query, texts).map(table=True)

        self.assertEqual(len(table), 3) # 2 element rows, 1 header row

        # assert first column
        self.assertEqual(self.el1, table[1][0])
        self.assertEqual(self.el2, table[2][0])

        self.assertEqual('', table[1][2]) # 1st element mapped to first text
        self.assertEqual('', table[2][1]) # 2nd element mapped to second text

if __name__ == '__main__':
    unittest.main()
