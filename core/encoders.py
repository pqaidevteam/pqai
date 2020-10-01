
class Encoder:

	"""Base class for making objects that encode one form of data into
	another form, e.g., text to tokens or text to vectors.
	"""

	def __init__(self, fn=None):
		self._encoder_fn = fn
		self._input_validation_fn = None
		self._name = 'Encoder'

	@property
	def encoder_fn(self):
		return self._encoder_fn
	
	@encoder_fn.setter
	def encoder_fn(self, fn):
		self._encoder_fn = fn

	@property
	def input_validation_fn(self):
		return self._input_validation_fn
	
	@input_validation_fn.setter
	def input_validation_fn(self, fn):
		self._input_validation_fn = fn

	def encode(self, item):
		self._can_encode(item)
		return self._encoder_fn(item)

	def encode_many(self, items):
		return [self.encode(item) for item in items]

	def _can_encode(self, data):
		if not callable(self._encoder_fn):
			self._raise_invalid_encoder_fn_exception()
		if not self.is_valid_input(data):
			self._raise_invalid_input_data_exception()

	def is_valid_input(self, data):
		is_valid = self._input_validation_fn
		return False if callable(is_valid) and not is_valid(data) else True

	def _raise_invalid_encoder_fn_exception(self):
		msg = f'{self._name} does not have valid encoding function.'
		raise Exception(msg)

	def _raise_invalid_input_data_exception(self):
		msg = f'Invalid input data for {self._name}.'
		raise Exception(msg)


class TokenSequenceEncoder(Encoder):

	"""Encoder for converting text into a list of tokens.
	"""
	
	def __init__(self, fn=None):
		super().__init__(fn)
		self._name = 'TokenSequenceEncoder'
		self._input_validation_fn = lambda x: isinstance(x, str)


class BagOfTokensEncoder(Encoder):

	"""Encoder for converting text into a bag of tokens (e.g., words).
	"""
	
	def __init__(self, fn=None):
		super().__init__(fn)
		self._name = 'BagOfTokensEncoder'
		self._input_validation_fn = lambda x: isinstance(x, str)

class EntityExtractor:

	def __init__(self):
		pass