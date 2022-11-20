import unittest
from pathlib import Path
import sys
from dotenv import load_dotenv

TEST_DIR = str(Path(__file__).parent.resolve())
BASE_DIR = str(Path(__file__).parent.parent.resolve())
ENV_FILE = f"{BASE_DIR}/.env"
load_dotenv(ENV_FILE)

sys.path.append(BASE_DIR)

from core.classifiers import BOWSubclassPredictor, BERTSubclassPredictor


class TestBOWSubclassPredictor(unittest.TestCase):
    "Tests for predicting the correct subclasses for the BOW-vectors based model"

    def test__can_classify(self):
        classifier = BOWSubclassPredictor()
        expected = ["G10L", "G06F", "G06Q", "H05K", "H01R"]
        actual = classifier.predict_subclasses("natural language processsing")
        self.assertEqual(expected, actual)


class TestBERTSubclassPredictor(unittest.TestCase):
    "Tests for predicting the correct subclasses for the BERT model"

    def test__can_classify(self):
        classifier = BERTSubclassPredictor()
        expected = ["G06F", "G10L", "G09B", "G06Q", "G06T"]
        actual = classifier.predict_subclasses("natural language processsing")
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
