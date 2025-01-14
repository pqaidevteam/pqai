import unittest
from fastapi.testclient import TestClient
import sys
import numpy as np
from pathlib import Path

THIS_DIR = Path(__file__).parent.resolve()
BASE_DIR = THIS_DIR.parent
SERVICES_DIR = BASE_DIR / "services"
sys.path.append(SERVICES_DIR.as_posix())

from vector_search import app

client = TestClient(app)

class TestVectorSearch(unittest.TestCase):

    def test__vector_search(self):
        vector = np.random.rand(384).tolist()
        payload = {
            "vector": vector,
            "indexes": 'all'
        }
        response = client.post("/search", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)
        for item in data:
            self.assertIsInstance(item, list)
            self.assertTrue(len(item) == 3)
            [doc_id, index_id, score] = item
            self.assertIsInstance(doc_id, str)
            self.assertIsInstance(index_id, str)
            self.assertIsInstance(score, float)


if __name__ == '__main__':
    unittest.main()
