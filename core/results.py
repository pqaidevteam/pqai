from core.documents import Document

class SearchResult (Document):

	def __init__(self, doc_id, index_id, score):
		super().__init__(doc_id)
		self._score = score
		self._index = index_id
		self.snippet = None
		self.mapping = None

	def __str__(self):
		return f'SearchResult: {self.id}, Score: {self.score}'

	def __repr__(self):
		return f'SearchResult: {self.id}, Score: {self.score}'

	@property
	def score(self):
		return self._score

	def json(self):
		json_obj = super().json()
		json_obj['score'] = self.score
		json_obj['snippet'] = self.snippet
		json_obj['mapping'] = self.mapping
		json_obj['index'] = self._index
		return json_obj

	def satisfies(self, conditions):
		return conditions.passed_by(self)