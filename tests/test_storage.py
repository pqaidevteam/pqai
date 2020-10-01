import unittest

import sys
from pathlib import Path
THIS_DIR = Path(__file__).parent
BASE_DIR = THIS_DIR.parent
sys.path.append(str(BASE_DIR.resolve()))

from core.storage import Storage, Folder, DocumentsFolder, MongoCollection
from pymongo import MongoClient

class TestStorageClass(unittest.TestCase):
	
	def test_retrieval(self):
		storage = Storage()
		storage.retrieval_fn = lambda x: f'{x} found'
		item_spec = 'doc_1'
		expected = 'doc_1 found'
		actual = storage.get(item_spec)
		self.assertEqual(expected, actual)

	def test_storage(self):
		buff = {}
		
		def store(item_spec, item):
			buff[item_spec] = item
		
		def retrieve(item_spec):
			return buff[item_spec]
		
		storage = Storage()
		storage.storage_fn = store
		storage.retrieval_fn = retrieve
		item_spec = 'greeting'
		item = 'Hey, there!'
		storage.save(item_spec, item)
		self.assertEqual(item, storage.get(item_spec))


class TestFolderClass(unittest.TestCase):
	
	def test_can_save_and_retrieve_file(self):
		folder = Folder(str(THIS_DIR.resolve()))
		folder.save('test_file', 'test_contents')
		contents = folder.get('test_file')
		self.assertEqual('test_contents', contents)


class TestDocumentsFolder(unittest.TestCase):
	
	def test_can_save_and_retrieve_document(self):
		folder = DocumentsFolder(str(THIS_DIR.resolve()))
		folder.save('test_doc', { 'title': 'test doc title' })
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