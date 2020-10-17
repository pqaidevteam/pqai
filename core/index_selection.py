from core.classifiers import BERTSubclassPredictor
from config.config import indexes_dir

class SublassesBasedIndexSelector():
	
	def __init__(self, indexes):
		self._indexes = indexes
		self._subclass_predict_fn = BERTSubclassPredictor().predict_subclasses

	def select(self, text, n=5):
		subclasses = self._subclass_predict_fn(text)
		subclasses = subclasses[:n]
		indexes = []
		for subclass in subclasses:
			indexes += self._indexes.get(subclass)
		return indexes
