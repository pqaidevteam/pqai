import unittest
from core.db import patent_db, npl_db

class TestDB(unittest.TestCase):

    def test__can_fetch_patent_data(self):
        pn = "US11856900B2"
        data = patent_db.get(pn)
        self.assertIsInstance(data, dict)
        self.assertEqual(data['publicationNumber'], pn)
        self.assertTrue(data['title'].startswith("Selective"))
    
    def test__can_fetch_non_US_patent_data(self):
        pn = "KR20240000532A"
        data = patent_db.get(pn)
        self.assertIsInstance(data, dict)
        self.assertEqual(data['publicationNumber'], pn)
        self.assertTrue(data['title'].startswith("Anti-nectin-4"))
    
    def test__can_fetch_npl_data(self):
        doc_id = "W4390534784"
        data = npl_db.get(doc_id)
        self.assertIsInstance(data, dict)
        self.assertEqual(data['id'], doc_id)
        self.assertTrue(data['title'].startswith("Characteristics"))
    
    def test__can_fetch_multiple_documents(self):
        doc_ids = ["US11856899B2", "W4390534784", "US11856900B2"]
        results = patent_db.get(doc_ids)
        self.assertEqual(len(results), 3)
        self.assertTrue(all(isinstance(res, dict) for res in results))
        self.assertEqual(results[0]['publicationNumber'], "US11856899B2")
        self.assertEqual(results[1]['id'], "W4390534784")
        self.assertEqual(results[2]['publicationNumber'], "US11856900B2")


if __name__ == '__main__':
    unittest.main()
