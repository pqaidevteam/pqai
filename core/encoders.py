from config.config import models_dir
from core import utils
import re
import numpy as np

class Encoder:

	"""Base class for making objects that encode one form of data into
	another form, e.g., text to tokens or text to vectors.
	"""

	def __init__(self, fn=None):
		self._encoder_fn = fn
		self._input_validation_fn = None
		self._name = 'Encoder'

	def set_encoding_fn(self, fn):
		self._encoder_fn = fn

	def set_input_validation_fn(self, fn):
		self._input_validation_fn = fn

	def encode(self, item):
		self._raise_exception_if_incompatible(item)
		return self._encoder_fn(item)

	def encode_many(self, items):
		return [self.encode(item) for item in items]

	def _raise_exception_if_incompatible(self, data):
		if not callable(self._encoder_fn):
			self._raise_invalid_encoder_fn_exception()
		if not self.can_encode(data):
			self._raise_invalid_input_data_exception()

	def can_encode(self, data):
		is_valid = self._input_validation_fn
		return False if callable(is_valid) and not is_valid(data) else True

	def _raise_invalid_encoder_fn_exception(self):
		msg = f'{self._name} does not have valid encoding function.'
		raise Exception(msg)

	def _raise_invalid_input_data_exception(self):
		msg = f'Invalid input data for {self._name}.'
		raise Exception(msg)


class BagOfEntitiesEncoder(Encoder):

	@classmethod
	def from_vocab_file(self, filepath):
		encoder = BagOfEntitiesEncoder()
		encoder._vocab_file = filepath
		return encoder

	def __init__(self):
		super().__init__()
		self._name = 'BagOfEntitiesEncoder'
		self.set_encoding_fn(self._get_entities)
		self.set_input_validation_fn(lambda x: isinstance(x, str))
		self._vocab_file = None
		self._vocab = None
		self._lookup_table = None
		self._no_casing = True
		self._maxlen = 3
		self._separator = ' '
		self._sent_tokenizer = utils.get_sentences

	def set_maxlen(self, n):
		self._maxlen = n

	def set_separator(self, sep):
		self._separator = sep

	def _load_vocab(self):
		with open(self._vocab_file) as fp:
			self._vocab = fp.read().strip().splitlines()
			self._lookup_table = set(self._vocab)

	def _load_vocab_if_unloaded(self):
		if not isinstance(self._vocab, list):
			self._load_vocab()

	def _get_entities(self, text):
		self._load_vocab_if_unloaded()
		entities = []
		for sent in self._sent_tokenizer(text):
			entities += self._get_entities_from_sentence(sent)
		return set(entities)

	def _get_entities_from_sentence(self, sentence):
		candidates = self._get_candidate_entities(sentence)
		return [c for c in candidates if c in self._lookup_table]

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
		pattern = r'([\w\-]+|\W+)'
		matches = re.findall(pattern, text)
		tokens = [m for m in matches if m.strip()]
		return tokens


class EmbeddingMatrix():

	def __init__(self, vocab=None, vectors=None):
		self._items = None
		self._vectors = None
		self._lookup = None
		self._unit_vectors = None

	@property
	def dims(self):
		if self._vectors is None:
			return None
		vec = self._vectors[0]
		return len(vec)

	def __getitem__(self, key):
		idx = self._lookup[key]
		return self._vectors[idx]

	def similar_to(self, item, n=10):
		item_vector = self[item]
		cosine_prods = np.dot(item_vector, self._unit_vectors.T)
		idxs = np.argsort(cosine_prods)[:n][::-1]
		return [self._items[i] for i in idxs]

	@classmethod
	def from_tsv(self, filepath):
		emb = EmbeddingMatrix()
		emb._load_from_tsv_file(filepath)
		return emb

	def _load_from_tsv_file(self, filepath):
		pairs = self._parse_tsv_file(filepath)
		self._items = [word for word, _ in pairs]
		self._vectors = np.array([vector for _, vector in pairs])
		self._lookup = {w:i for i,w in enumerate(self._items)}
		self._unit_vectors = self._normalize_vectors(self._vectors)

	def _parse_tsv_file(self, filepath):
		with open(filepath) as file:
			lines = (l for l in file if l.strip())
			pairs = [self._parse_tsv_line(l) for l in lines]
		return pairs

	def _parse_tsv_line(self, line):
		[word, *vector] = line.strip().split('\t')
		vector = [float(val) for val in vector]
		return word, vector

	def _normalize_vectors(self, M):
		epsilon = np.finfo(float).eps
		norms = np.sqrt((M*M).sum(axis=1, keepdims=True))
		norms += epsilon	# to avoid division by zero
		return M / norms


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