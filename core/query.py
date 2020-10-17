
from core.indexes import Index

class Query():

	def __init__(self, query):
		self._query = query

	def run(self, index, n):
		return index.search(self._query, n)


class TextQuery(Query):

	def __init__(self, text):
		super().__init__(text)


class VectorQuery(Query):

	def __init__(self, vector):
		super().__init__(vector)