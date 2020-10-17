from core.documents import Document

class SearchResult (Document):

	def __init__(self, doc_id, index_id, score):
		super().__init__(doc_id)
		self._score = score
		self._index = index_id
		self._snippet = None
		self._mapping = None

	def __str__(self):
		return f'SearchResult: {self.id}, Score: {self.score}'

	def __repr__(self):
		return f'SearchResult: {self.id}, Score: {self.score}'

	@property
	def score (self):
		return self._score

	@property
	def snippet(self):
		return self._snippet

	@property
	def mapping(self):
		return self._mapping
	
	@snippet.setter
	def snippet(self, value):
		self._snippet = value

	@mapping.setter
	def mapping(self, value):
		self._mapping = value

	def json (self):
		json_obj = super().json()
		json_obj['score'] = self.score
		json_obj['snippet'] = self.snippet
		json_obj['mapping'] = self.mapping
		json_obj['index'] = self._index
		return json_obj

	def passes_through (self, conditions):
		return conditions.apply(self)