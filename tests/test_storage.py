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

from core.storage import Storage, Folder, JSONDocumentsFolder, MongoCollection
from pymongo import MongoClient

class TestFolderClass(unittest.TestCase):
	
	def test_can_save_and_retrieve_file(self):
		folder = Folder(TEST_DIR)
		folder.put('test_file', 'test_contents')
		contents = folder.get('test_file')
		self.assertEqual('test_contents', contents)


class TestJSONDocumentsFolder(unittest.TestCase):
	
	def test_can_save_and_retrieve_document(self):
		folder = JSONDocumentsFolder(TEST_DIR)
		folder.put('test_doc', { 'title': 'test doc title' })
		retrieved = folder.get('test_doc')
		self.assertEqual({ 'title': 'test doc title' }, retrieved)


class TestMongoDBClass(unittest.TestCase):
	
	def test_can_retrieve_document(self):
		client = MongoClient('localhost', 27017)
		query = { 'publicationNumber': 'US7654321B2' }
		mongo_coll = MongoCollection(client.pqai.bibliography)
		doc = mongo_coll.get(query)
		self.assertEqual('US7654321B2', doc['publicationNumber'])


if __name__ == '__main__':
    unittest.main()