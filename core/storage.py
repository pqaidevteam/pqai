import json


class Storage:

	def __init__(self):
		self._retrieval_fn = None
		self._storage_fn = None

	@property
	def retrieval_fn(self):
		return self._retrieval_fn

	@retrieval_fn.setter
	def retrieval_fn(self, fn):
		self._retrieval_fn = fn

	@property
	def storage_fn(self):
		return self.storage_fn

	@storage_fn.setter
	def storage_fn(self, fn):
		self._storage_fn = fn

	def get(self, item_spec):
		return self._retrieval_fn(item_spec)

	def save(self, item_spec, item):
		self._storage_fn(item_spec, item)


class Folder(Storage):
	
	def __init__(self, path:str):
		self._base_dir = path if path.endswith('/') else path + '/'
		self._retrieval_fn = self._get_file
		self._storage_fn = self._save_file

	def _get_file(self, relative_path:str):
		path = self._get_abs_path(relative_path)
		with open(path) as fp:
			return fp.read()

	def _save_file(self, relative_path:str, contents:str):
		path = self._get_abs_path(relative_path)
		with open(path, 'w') as fp:
			return fp.write(contents)

	def _get_abs_path(self, relative_path:str):
		return self._base_dir + relative_path


class DocumentsFolder(Folder):

	"""A folder containing flat JSON files as documents.
	"""
	
	def __init__(self, path:str):
		super().__init__(path)
		self._file_extension = '.json'

	def get(self, doc_id:str):
		filename = self._doc_id_to_filename(doc_id)
		contents = super()._get_file(filename)
		return json.loads(contents)

	def save(self, doc_id:str, doc_data:dict):
		filename = self._doc_id_to_filename(doc_id)
		contents = json.dumps(doc_data)
		super()._save_file(filename, contents)

	def _doc_id_to_filename(self, doc_id:str):
		return doc_id + self._file_extension


class MongoCollection(Storage):
	
	def __init__(self, mongo_collection):
		self._collection = mongo_collection
		self._retrieval_fn = self._run_query
		self._storage_fn = None

	def _run_query(self, query):
		return self._collection.find_one(query)

	