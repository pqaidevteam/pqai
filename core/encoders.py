from config.config import models_dir
from core import utils
import re
import numpy as np

from core.representations import BagOfEntities

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
		self._separator = '_'
		self._sent_tokenizer = utils.get_sentences
		self._non_overlapping = True

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
		entities = set(entities)
		if self._non_overlapping:
			entities = BagOfEntities(entities).non_overlapping()
		return entities

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

	"""A wrapper on a collection of items and their embeddings. It
	provides easy retrieval of embedding of any vector and retrieval of
	items similar to a given item on the basis of the similarity of their
	vectors.

	It can be used to store such data as word, entity, or document
	embeddings.
	"""
	
	def __init__(self, items, vectors):
		"""Create an `EmbeddingMatrix` object with the given `items` and
		`vectors`.
		
		Args:
		    items (list): List of items, which can be `str`, `int` or
		    	any other hashable data types.
		    vectors (np.ndarray): A 2-D matrix with rows as numerous as
		    	the number of items and columns corresponding to the
		    	vector dimensions.
		"""
		self._items = items
		self._vectors = vectors
		self._lookup = self._create_lookup()
		self._unit_vectors = self._create_unit_vectors()

	@property
	def dims(self):
		"""Return dimensionality of embeddings (vectors).
		
		Returns:
		    int: Dimensionality of vectors
		"""
		vec = self._vectors[0]
		return len(vec)

	def __getitem__(self, item):
		"""Get vector for an item.
		
		Args:
		    item (str or int): Item identifier
		
		Returns:
		    np.ndarray: Item vector
		"""
		idx = self._lookup[item]
		return self._vectors[idx]

	def __contains__(self, item):
		"""Check whether given item has an embedding in the matrix.
		
		Args:
		    item (str or int): Item
		
		Returns:
		    bool: True if embedding exists, False otherwise
		"""
		return item in self._lookup

	def similar_to(self, item, n=10):
		"""Get a list of `n` most similar items to the given `item`.
		
		Args:
		    item (str or int): Item identifier
		    n (int, optional): Number of items to return
		
		Returns:
		    list: List of items; if fewer than `n` items are present,
		    	then a fewer items will be returned
		"""
		idx = self._lookup[item]
		item_vector = self._unit_vectors[idx]
		cosine_prods = np.dot(item_vector, self._unit_vectors.T)
		idxs = np.argsort(cosine_prods)[::-1][1:n+1]
		return [self._items[i] for i in idxs]

	def _normalize_vectors(self, M):
		"""Normalize rows of the given 2-D matrix by dividing with their
		respective magnitudes.
		
		Args:
		    M (np.ndarray): A 2-D numpy matrix
		
		Returns:
		    np.ndarray: A matrix whose rows are unit vectors which
		    	correspond to the rows of the input matrix
		"""
		epsilon = np.finfo(float).eps
		norms = np.sqrt((M*M).sum(axis=1, keepdims=True))
		norms += epsilon	# to avoid division by zero
		return M / norms

	def _create_lookup(self):
		"""Create a dictionary for finding the index of any item in the
		items list.
		
		Returns:
		    dict: Dictionary, whose keys are items, values are integer
		    	indexes
		"""
		return {w:i for i,w in enumerate(self._items)}

	def _create_unit_vectors(self):
		"""Create unit vector matrix of the item vectors (which are
		used to find similar items).
		
		Returns:
		    np.ndarray: A matrix corresponding to vector matrix of the
		    	items but this one has unit vectors.
		"""
		return self._normalize_vectors(self._vectors)

	@classmethod
	def from_txt_npy(self, txt_filepath, npy_filepath):
		"""Create an `EmbeddingMatrix` from an items file containing the
		a list of item descriptions (one per line) and a numpy file with
		the vectors that have one-to-one correspondance with the items.
		
		Args:
		    txt_filepath (str): Path to items file
		    npy_filepath (str): Path to numpy (vectors) file
		
		Returns:
		    EmbeddingMatrix: Resulting embedding matrix object
		"""
		with open(txt_filepath) as file:
			items = [l.strip() for l in file if l.strip()]
		vectors = np.load(npy_filepath)
		return EmbeddingMatrix(items, vectors)
	
	@classmethod
	def from_tsv(self, filepath):
		"""Create an `EmbeddingMatrix` from a tsv file where the first
		column contains the item descriptions and subsequent columns
		contain the vector components. All columns should be separated
        by single tabs.
		
		Args:
		    filepath (str): Path to tsv (tab separated values) file
		
		Returns:
		    EmbeddingMatrix: Resulting embedding matrix object
		"""
		pairs = self._parse_tsv_file(filepath)
		items = [word for word, _ in pairs]
		vectors = np.array([vector for _, vector in pairs])
		return EmbeddingMatrix(items, vectors)

	@classmethod
	def _parse_tsv_file(self, filepath):
		with open(filepath) as file:
			lines = (l for l in file if l.strip())
			pairs = [self._parse_tsv_line(l) for l in lines]
		return pairs

	@classmethod
	def _parse_tsv_line(self, line):
		[word, *vector] = line.strip().split('\t')
		vector = [float(val) for val in vector]
		return word, vector


class BagOfVectorsEncoder(Encoder):
	
	def __init__(self, emb_matrix):
		super().__init__()
		self._emb_matrix = emb_matrix
		self.set_encoding_fn(self._vectorize_items)

	def _vectorize_items(self, bag_of_items):
		items = [item for item in bag_of_items if item in self._emb_matrix]
		vectors = [self._emb_matrix[item] for item in items]
		vectors_as_tuples = [tuple(vec) for vec in vectors]
		return set(vectors_as_tuples)


class BagOfWordsEncoder(Encoder):
	
	def __init__(self, fn=None):
		super().__init__(fn)
		self._name = 'BagOfTokensEncoder'
		self._input_validation_fn = lambda x: isinstance(x, str)


class VectorSequenceEncoder():
	pass


class TokenSequenceEncoder(Encoder):
	
	def __init__(self, fn=None):
		super().__init__(fn)
		self._name = 'TokenSequenceEncoder'
		self._input_validation_fn = lambda x: isinstance(x, str)