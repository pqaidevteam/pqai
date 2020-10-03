from config.config import models_dir
from core import utils
import re

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
	
	def __init__(self, fn=None):
		super().__init__(fn)
		self._name = 'TokenSequenceEncoder'
		self._input_validation_fn = lambda x: isinstance(x, str)


class BagOfWordsEncoder(Encoder):
	
	def __init__(self, fn=None):
		super().__init__(fn)
		self._name = 'BagOfTokensEncoder'
		self._input_validation_fn = lambda x: isinstance(x, str)


class BagOfEntitiesEncoder(Encoder):

	def __init__(self):
		super().__init__(self._get_entities)
		self._name = 'BagOfEntitiesEncoder'
		self._vocab = None
		self._lut = None
		self._no_casing = True
		self._maxlen = 3
		self._separator = ' '
		self._vocab_file = models_dir + 'entities.txt'
		self._sent_tokenizer = utils.get_sentences
		self._input_validation_fn = lambda x: isinstance(x, str)

	def _load_vocab_from_txt_file(self):
		with open(self._vocab_file) as fp:
			self._vocab = fp.read().strip().splitlines()
			self._lut = set(self._vocab)

	def _load_vocab_if_unloaded(self):
		if isinstance(self._vocab, list):
			return
		self._load_vocab_from_txt_file()

	def _get_entities(self, text):
		self._load_vocab_if_unloaded()
		entities = []
		for sent in self._sent_tokenizer(text):
			entities += self._get_entities_from_sentence(sent)
		return set(entities)

	def _get_entities_from_sentence(self, sentence):
		candidates = self._get_candidate_entities(sentence)
		return [c for c in candidates if c in self._lut]

	def _get_candidate_entities(self, sent):
		candidates = set()
		tokens = self._tokenize(sent)
		for n in range(1, self._maxlen+1):
			for n_gram in self._get_n_grams(n, tokens):
				candidates.add(n_gram)
		return candidates

	def _get_n_grams(self, n, tokens):
		if len(tokens) < n:
			return []
		sep = self._separator
		n_grams = [sep.join(tokens[i:i+n]) for i in range(len(tokens))]
		return n_grams

	def _tokenize(self, text):
		text = text.lower() if self._no_casing else text
		pattern = r'(\w+|\W+)'
		matches = re.findall(pattern, text)
		tokens = [m for m in matches if m.strip()]
		return tokens