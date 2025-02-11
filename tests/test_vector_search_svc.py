import os
import unittest
from fastapi.testclient import TestClient
import sys
from pathlib import Path
from dotenv import load_dotenv

THIS_DIR = Path(__file__).parent.resolve()
BASE_DIR = THIS_DIR.parent
SERVICES_DIR = BASE_DIR / "services"
sys.path.append(SERVICES_DIR.as_posix())

load_dotenv(BASE_DIR / ".env")
os.environ['ENVIRONMENT'] = 'test'

from vector_search import app
from core.vectorizers import SentBERTVectorizer

vectorizer = SentBERTVectorizer()

class TestVectorSearch(unittest.TestCase):

    def test__vector_search(self):
        query = "fire fighting drones"
        vector = vectorizer.embed(query).tolist()
        with TestClient(app) as client:
            payload = {
                "vector": vector,
                "n_results": 10
            }
            response = client.post("/search", json=payload)
            self.assertValidResponse(response)

            payload = {
                "vector": vector,
                "n_results": 10,
                "type": "patent"
            }
            response = client.post("/search", json=payload)
            self.assertValidResponse(response)
            for result in response.json():
                idx = result[1]
                self.assertIn("patent", idx)
            
            payload = {
                "vector": vector,
                "n_results": 10,
                "type": "npl"
            }
            response = client.post("/search", json=payload)
            self.assertValidResponse(response)
            for result in response.json():
                idx = result[1]
                self.assertIn("npl", idx)
            
            payload = {
                "vector": vector,
                "n_results": 25,
                "type": "patent"
            }
            response = client.post("/search", json=payload)
            self.assertValidResponse(response)
            results = response.json()
            self.assertTrue(len(results) >= 25)
        
    def assertValidResponse(self, response):
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)
        for item in data:
            self.assertIsInstance(item, list)
            self.assertTrue(len(item) == 3)
            doc_id, index_id, score = item
            self.assertIsInstance(doc_id, str)
            self.assertIsInstance(index_id, str)
            self.assertIsInstance(score, float)
            for i in range(1, len(data)):
                self.assertTrue(data[i][2] <= data[i-1][2])


if __name__ == '__main__':
    unittest.main()
