from core.documents import Document, Patent
from core.classifiers import BOWSubclassPredictor
from collections import Counter
import re

class SearchResult (Document):

	def __init__(self, doc_id, index_id, score):
		super().__init__(doc_id)
		self._score = score
		self._index = index_id
		self.snippet = None
		self.mapping = None
		self.image = None

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

	def _is_subclass(self, string):
		return bool(re.match(r'^[A-HY]\d\d[A-Z]$', string))

	def _assign_index(self):
		if self._is_subclass(self._index[:4]):
			return self._index

		if self.type == 'patent':
			cpcs = Patent(self.id).cpcs
			if cpcs:
				subclasses = [cpc[:4] for cpc in cpcs]
				return Counter(subclasses).most_common(1)[0][0]

		return BOWSubclassPredictor().predict_subclasses(self.abstract)[0]

	def satisfies(self, conditions):
		return conditions.passed_by(self)