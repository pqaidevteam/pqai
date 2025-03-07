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

    def setUp(self):
        self.pns = [
            "US7654321B2",
            "US20070205188A1",
            "US2007205188A1"
        ]

    def test__can_check_type(self):
        for pn in self.pns:
            doc = Document(pn)
            self.assertEqual(doc.type, 'patent')
            self.assertEqual('patent', doc.type)

    def test__can_compare_publication_date(self):
        doc = Document("US7654321B2")
        d_before = "2010-02-01"
        d_after = "2010-02-03"
        d_publication = "2010-02-02"

        self.assertTrue(doc.is_published_before(d_after))
        self.assertFalse(doc.is_published_after(d_after))

        self.assertFalse(doc.is_published_before(d_publication))
        self.assertFalse(doc.is_published_after(d_publication))

        self.assertFalse(doc.is_published_before(d_before))
        self.assertTrue(doc.is_published_after(d_before))

        self.assertTrue(doc.is_published_between(d_before, d_after))
        self.assertFalse(doc.is_published_between(d_before, d_publication))
        self.assertFalse(doc.is_published_between(d_publication, d_after))

    def test__can_get_text_fields(self):
        doc = Document("US7654321B2")
        title = "Formation fluid sampling apparatus and methods"
        self.assertEqual(title, doc.title)
        self.assertEqual(753, len(doc.abstract))

    def test__can_get_publication_date(self):
        doc = Document("US7654321B2")
        self.assertEqual("2010-02-02", doc.publication_date)

    def test__can_get_www_link(self):
        for pn in self.pns:
            doc = Document(pn)
            self.assertIsInstance(doc.www_link, str)

    def test__can_get_assignee(self):
        for pn in self.pns:
            doc = Document(pn)
            self.assertIsInstance(doc.owner, str)

    def test__can_get_publication_id(self):
        doc = Document("US7654321B2")
        self.assertEqual(doc.publication_id, "US7654321B2")
        
        doc = Document("US20070205188A1")
        self.assertEqual(doc.publication_id, "US2007205188A1") # how it's in the database

        doc = Document("US2007205188A1")
        self.assertEqual(doc.publication_id, "US2007205188A1")

    def test__can_get_full_text(self):
        for pn in self.pns:
            doc = Document(pn)
            self.assertIsInstance(doc.full_text, str)

    def test__can_get_inventors(self):
        for pn in self.pns:
            doc = Document(pn)
            self.assertIsInstance(doc.inventors, list)

    def test__can_get_alias(self):
        for pn in self.pns:
            doc = Document(pn)
            self.assertIsInstance(doc.alias, str)

    def test__can_get_json_repr(self):
        for pn in self.pns:
            doc = Document(pn)
            json_data = doc.json()
            self.assertIsInstance(json_data, dict)
            self.assertIn("id", json_data)
            self.assertIn("type", json_data)
            self.assertIn("publication_id", json_data)
            self.assertIn("title", json_data)
            self.assertIn("abstract", json_data)
            self.assertIn("publication_date", json_data)
            self.assertIn("www_link", json_data)
            self.assertIn("owner", json_data)
            self.assertIn("image", json_data)
            self.assertIn("alias", json_data)
            self.assertIn("inventors", json_data)


if __name__ == '__main__':
    unittest.main()