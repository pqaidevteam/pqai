from core.classifiers import BERTSubclassPredictor

class SublassesBasedIndexSelector():

	_subclass_predict_fn = BERTSubclassPredictor().predict_subclasses
	
	def __init__(self, indexes):
		self._indexes = indexes

	def select(self, text, n=3):
		subclasses = self._subclass_predict_fn(text)
		subclasses = subclasses[:n]
		indexes = []
		for subclass in subclasses:
			indexes += self._indexes.get(subclass)
		return indexes
