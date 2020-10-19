import numpy as np
from nltk.tokenize import RegexpTokenizer
import math
import numba
import re
import json
from sklearn.decomposition import TruncatedSVD

from core.utils import is_cpc_code, is_patent_number
from config.config import models_dir
from core.db import get_patent_data
from config.config import models_dir as MODELS_DIR


class GloveWordEmbeddings():
    
    def __init__(self):
        self.models_dir = MODELS_DIR
        self.vocab_file = self.models_dir + '/glove-vocab.json'
        self.dict_file = self.models_dir + '/glove-dictionary.json'
        self.dfs_file = self.models_dir + '/dfs.json'
        self.embeddings_file = self.models_dir + '/glove-We.npy'
        self.vocab = None
        self.dictionary = None
        self.dfs = None
        self.sifs = None
        self.embeddings = None
        self.dims = None
        self._load()
    
    def _load(self):
        with open(self.vocab_file) as file:
            self.vocab = json.load(file)
        with open(self.dict_file) as file:
            self.dictionary = json.load(file)
        with open(self.dfs_file) as file:
            self.dfs = json.load(file)
        self.embeddings = np.load(self.embeddings_file)
        self.sifs = { word:self.df2sif(word, self.dfs) for word in self.dfs }
        self.dims = self.embeddings.shape[1]
    
    def __len__(self):
        return self.embeddings.shape[0]
    
    @staticmethod
    def df2sif(word, dfs):
        n = dfs[word]
        N = dfs['the']
        p = n / N
        a = 0.01
        w = a / (a + p)
        return w
    
    def __getitem__(self, item):
        if type(item) is int:
            return self.embeddings[item]
        elif type(item) is str:
            item = item if item in self.dictionary else '<unk>'
            return self.embeddings[self.dictionary[item]]
        else:
            return np.zeros(self.dims)
    
    def get_sif (self, word):
        return self.sifs.get(word, 1.0)


class Embeddings():

    """Base class for a collection of items and their corresponding
       vectors, e.g., word embeddings obtained from word2vec or GloVe.
    
    Attributes:
        items (list): Item labels
        vectors (iterable): An array of item vectors
    """
    
    def __init__(self, items, vectors):
        """Initialize
        
        Args:
            items (list): Labels with which items are identified. Labels
                must be hashable (used in an internal dictionary).
            vectors (ndarray): An array containing vectors for items in
                the same sequence as the in the `items` list.
        
        Raises:
            Exception: if the number of items are NOT equal to the
                number of vectors, i.e., lack of one-to-one mapping
                between items and vectors.
        """
        if len(items) != len(vectors):
            raise Exception('Unequal number of items and vectors.')

        self.items = items
        self.vectors = vectors
        self._dict = self._make_dict(self)

    def _make_dict(self):
        """Make a dictionary for quick look up of item vectors.
        """
        self._dict = { item: i for i, item in enumerate(self.items) }

    def __getitem__(self, item):
        """Get the vector for given item.
        
        Args:
            item (str): Item label
        
        Returns:
            ndarray: Item vector
        """
        i = self._dict[item]
        return self.vectors[i]


class WordEmbeddings(Embeddings):

    """Class for collection of word embeddings.
    
    Attributes:
        PAD (str): Label for the padding token
        UNK (str): Label for the unknown token
    """
    
    def __init__(self, words, embeddings, pad='<pad>', unk='<unk>'):
        """Initialize word embeddings
        
        Args:
            words (list): Words
            embeddings (ndarray): Word embeddings (vectors)
            pad (str, optional): Label for the padding token, usually
                filled in empty places in a string having fewer words
                than the required sequence length
            unk (str, optional): Label for the unknown tokens
        """
        super().__init__(items, embeddings)
        self.PAD = pad
        self.UNK = unk

    def __getitem__(self, word):
        """Return vector for a given word.

        If the vector for the given word isn't known, then the vector
        for the unknown token `<unk>` is returned.
        
        Args:
            word (str): A word
        
        Returns:
            ndarray: The vector corresponding to the given word
        """
        if word not in self._dict:
            return self.__getitem__(self.UNK)
        return super().__getitem__(word)


class Text(str):
    def __init__(self, text):
        self._text = text
        self._default_tokenizer = RegexpTokenizer(r'\w+')
    
    def to_tokens(self, tokenizer=None):
        if not tokenizer:
            tokenizer = self._default_tokenizer
        tokens = tokenizer.tokenize(self._text_lower)
        return TokenSequence(tokens)
    
    @property
    def _text_lower(self):
        return self._text.lower()
    
    def __repr__(self):
        prefix = 'Text: '
        if len(self._text) < 77:
            return prefix + self._text
        else:
            return prefix + self._text[:17] + '...'


class TokenSequence(list):
    def __init__(self, tokens):
        super().__init__(tokens)
        self._tokens = tokens
    
    def to_vector_sequence(self, token_embeddings):
        vectors = [token_embeddings[token] for token in self._tokens]
        return VectorSequence(self._tokens, vectors)
    
    @property
    def tokens(self):
        return self._tokens


class VectorSequence():
    def __init__(self, labels, vectors):
        self._labels = labels
        self._sequence = np.array(vectors)
        self._n = len(vectors)
        self._dims = self._sequence.shape[1]
        self._fixed_length = None
        self._default_interaction = Interaction()
        self._default_interaction.metric = 'cosine'
        self._default_interaction.amplify = False
        self._default_interaction.reinforce = True
        self._default_interaction.context = True
        self._default_interaction.window = 5
    
    @property
    def labels(self):
        return self._labels
    
    def __repr__(self):
        text = f'VectorSequence: {len(self._labels)} labels, {len(self._sequence)} vectors;'
        text += f' Labels: {", ".join(self._labels[:5])}'
        text += ', ...' if self._labels[5:] else ''
        return text
    
    def _weighted_by_tokens(self, weights):
        W = [weights[token] for token in self._tokens]
        return self.weighted_by_vectors(W)
    
    def _weighted_by_vectors(self, W):
        W = np.array(W).reshape(1, -1)
        return self._sequence * W.T
    
    def weigh(self, weights):
        if isinstance(weights, dict):
            self._weighted_by_tokens(weights)
        self._weighted_by_vector(weights)
    
    @property
    def redundancy_vector(self):
        interact = self._default_interaction.interact
        interactions = interact(self, self)
        interactions = np.tril(interactions._matrix, -1)
        return np.max(interactions, axis=1)
    
    @property
    def matrix(self):
        if self._fixed_length is None:
            return self._sequence
        if self._n > self._fixed_length:
            return self._truncated
        else:
            return self._padded

    @property
    def _truncated(self):
        return self._sequence[:self._fixed_length]

    @property
    def _padded(self):
        r = self._fixed_length - self._n
        shape = (r, self._dims)
        padding = np.zeros(shape)
        return np.concatenate((self._sequence, padding))

    def set_length(self, n):
        self._fixed_length = n
        return self

    @property
    def normalized_matrix(self):
        row_magnitudes = np.sqrt(np.sum(self._sequence*self._sequence, axis=1, keepdims=True))
        row_magnitudes += np.finfo(float).eps
        return self._sequence / row_magnitudes


class Interaction():
    
    def __init__(self, metric='cosine', context=False, amplify=False, reinforce=False, window=5):
        self.metric = metric
        self.context = context
        self.amplify = amplify
        self.reinforce = reinforce
        self.window_size = window
        self._amplify_matrix =  np.vectorize(self._amplify)
        self._a = 3.2
        self._b = 7.5
        self._c = 0.46
        self._f = 1.0
        self._h = 0.0
    
    def _dot_interaction(self, A, B):
        return np.matmul(A, B.T)
    
    def _cosine_interaction(self, A, B):
        An = self._normalize_rows(A)
        Bn = self._normalize_rows(B)
        return self._dot_interaction(An, Bn)
    
    def _euclidean_interaction(self, A, B):
        diff = A-B
        sq_diff = diff*diff
        return np.sqrt(sq_diff)
    
    def _context_sequence(self, vector_seq):
        M = vector_seq.matrix
        C = np.zeros(M.shape)
        C *= np.array([sifs[word] if word in sifs else 1.0
                       for word in vector_seq.labels]).reshape((-1, 1))
        r = min(len(M-1), self.window_size+1)
        for i in range(1, r):
            C[i:,:] += M[:-i,:]
            C[:-i,:] += M[i:,:]
        return C

    def interact(self, vector_seq_A, vector_seq_B):
        A = vector_seq_A.matrix
        B = vector_seq_B.matrix
        I = self.interaction_fn(A, B)
        I = self._amplifier(I) if self.amplify else I
        
        if not self.context:
            return InteractionMatrix(I)
        
        Ac = self._context_sequence(vector_seq_A)
        Bc = self._context_sequence(vector_seq_B)
        Ic = self.interaction_fn(Ac, Bc)
        Ic = self._amplifier(Ic) if self.amplify else Ic
        
        if not self.reinforce:
            return InteractionMatrix(I+Ic)
        
        M = self._reinforce(I, Ic)
        return InteractionMatrix(M)
    
    @property
    def interaction_fn(self):
        if self.metric == 'cosine':
            return self._cosine_interaction
        elif self.metric == 'dot':
            return self._dot_interaction
        elif self.metric == 'euclidean':
            return self._euclidean_interaction
    
    @staticmethod
    def _normalize_rows(M):
        row_magnitudes = np.sqrt(np.sum(M*M, axis=1, keepdims=True))
        row_magnitudes += np.finfo(float).eps
        return M / row_magnitudes
    
    @staticmethod
    def _reinforce(A, B):
        return 0.25*(A + B + 2*(A*B))
    
    def _amplify(self, x):
        return self._h + (self._f/(1+(self._a*math.exp(self._b*(x-self._c)))))
    
    @staticmethod
    @numba.vectorize([numba.float64(numba.float64)])
    def _amplifier(x):
        return 1/(1+(3.2*math.exp(-7.5*(x-0.46))))


class InteractionMatrix():
    
    def __init__(self, I):
        self._matrix = I
    
    def available_metrics(self):
        return self._available_interactions
    
    def maxpool(self, direction='horizontal'):
        axis = 1 if direction == 'horizontal' else 0
        return np.max(self._matrix, axis=axis)

embeddings = GloveWordEmbeddings()
sifs = embeddings.sifs


from scipy.spatial import distance
from core.utils import normalize_rows

class BagOfVectors():
    
    def __init__(self, vectors):
        self._vectors = vectors

    @classmethod
    def wmd(self, bov1, bov2, dist_fn=distance.cosine):
        n1 = len(bov1)
        n2 = len(bov2)
        if n1 == 0 or n2 == 0:
            return math.inf
        dists = np.zeros((n1, n2))
        for i, v1 in enumerate(bov1):
            for j, v2 in enumerate(bov2):
                dists[i, j] = dist_fn(v1, v2)
        return dists.min(axis=1).sum()

class BagOfEntities(set):

    def __init__(self, entities):
        super().__init__(entities)
        self._entities = set(entities)

    def non_overlapping(self):
        independent = set([])
        for entity in self._entities:
            if not self._is_part_of_another(entity):
                independent.add(entity)
        return independent

    def _is_part_of_another(self, entity):
        separator = r'[\_\s]'
        for target in self._entities:
            if target == entity:
                continue
            if re.search(rf'^{entity}{separator}', target):
                return True
            if re.search(rf'{separator}{entity}{separator}', target):
                return True
            if re.search(rf'{separator}{entity}$', target):
                return True
        return False

