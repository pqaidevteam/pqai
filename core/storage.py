import json


class Storage:

	def __init__(self):
		pass

	def get(self, item_id):
		pass

	def put(self, item_id, item):
		pass


class Folder(Storage):
	
	def __init__(self, path:str):
		self._base_dir = path if path.endswith('/') else path + '/'

	def get(self, relative_path:str):
		path = self._get_abs_path(relative_path)
		with open(path) as fp:
			return fp.read()

	def put(self, relative_path:str, contents:str):
		path = self._get_abs_path(relative_path)
		with open(path, 'w') as fp:
			return fp.write(contents)

	def _get_abs_path(self, relative_path:str):
		return self._base_dir + relative_path


class JSONDocumentsFolder(Folder):

	"""A folder containing flat JSON files as documents.
	"""
	
	def __init__(self, path:str):
		super().__init__(path)
		self._file_ext = '.json'

	def get(self, doc_id:str):
		filename = self._doc_id_to_filename(doc_id)
		contents = super().get(filename)
		return json.loads(contents)

	def put(self, doc_id:str, doc_data:dict):
		filename = self._doc_id_to_filename(doc_id)
		contents = json.dumps(doc_data)
		super().put(filename, contents)

	def _doc_id_to_filename(self, doc_id:str):
		return doc_id + self._file_ext


class MongoCollection(Storage):
	
	def __init__(self, mongo_collection):
		self._collection = mongo_collection

	def get(self, query):
		return self._collection.find_one(query)

	def put(self, item_id, item):
		pass

	