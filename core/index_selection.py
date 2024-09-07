from core.classifiers import BOWSubclassPredictor

class SubclassBasedIndexSelector():

	_subclass_predict_fn = BOWSubclassPredictor().predict_subclasses
	
	def __init__(self, indexes):
		self._indexes = indexes

	def select(self, text, n=3):
		subclasses = self._subclass_predict_fn(text)
		return subclasses[:n]
