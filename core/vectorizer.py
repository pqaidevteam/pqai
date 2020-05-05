import re
import numpy as np
import json
from sklearn.decomposition import TruncatedSVD

from core.gf import is_cpc_code, is_patent_number
from config.config import models_dir
from core.db import get_patent_data
from sentence_transformers import SentenceTransformer


# Files needed for cpc vectorization
cpc_list_file = models_dir + 'cpc_vectors_256d.items.json'
cpc_vecs_file = models_dir + 'cpc_vectors_256d.npy'

# Files needed for SIF text vectorization
word_vecs_file = models_dir + 'glove-We.npy'
word_list_file = models_dir + 'glove-vocab.json'
word_freq_file = models_dir + 'dfs.json'

# for DistilBERTVectorizer
distilbert_model_path = models_dir + 'vectorizer_distilbert_poc/'

class DistilBERTVectorizer:

    """ Singleton class used for vectorizing text spans using the
        DistilBERT model fine-tuned on the STS dataset and then PoC
        dataset.
    """
    
    class __impl:
        def __init__(self, path):
            self.model_dir = path
            self.model = None

        def load (self):
            self.model = SentenceTransformer(self.model_dir)

        def embed (self, text):
            """Vectorize a text span.
            
            Args:
                text (str): Text to be vectorized
            
            Returns:
                numpy.ndarray: 1D numpy vector
            """
            if self.model is None:
                self.load()
            vec = self.model.encode([text])[0]
            return vec

        def embed_arr (self, texts):
            """Vectorize a list of text spans (more efficient than
                repeatedly calling `self.embed`)
            
            Args:
                texts (lists): Texts to be vectorized
            
            Returns:
                numpy.ndarray: Matrix where rows are text vectors
            """
            if self.model is None:
                self.load()
            vecs = np.array(self.model.encode(texts))
            return vecs

    __instance = __impl(distilbert_model_path)

    def __getattr__(self, attr):
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        return setattr(self.__instance, attr, value)

    def __getitem__(self, key):
        return self.__instance.__getitem__(key)


class CPCVectorizer:

    """ Singleton class used for retrieving vector representation of CPC
        classes.
    """
    
    class __impl:
        def __init__(self, json_list_file, ann_vecs_file):
            self.vocab = json.load(open(json_list_file, 'r'))
            self.lut = {cpc:i for (i, cpc) in enumerate(self.vocab)}
            self.vecs = np.load(ann_vecs_file)
            self.dims = self.vecs.shape[1]
            self.gray = 0.00001 * np.ones(self.dims)

        def __getitem__(self, cpc_code):
            """Return vector representation of a cpc class.
            
            Args:
                cpc_code (str): CPC code, e.g. H04W72/02
            
            Returns:
                numpy.ndarray: One-dimensional vector representation of CPC
            """
            if cpc_code not in self.lut:
                return np.zeros(self.dims) 
            i = self.lut[cpc_code]
            return self.vecs[i]

        def embed (self, cpcs):
            """Summary
            
            Args:
                cpcs (list): Description
            
            Returns:
                numpy.ndarray: Description
            """
            if not [cpc for cpc in cpcs if cpc in self.lut]:
                return self.gray
            cpc_vecs = [self[cpc] for cpc in cpcs if cpc in self.lut]
            avg_cpc_vec = np.average(np.array(cpc_vecs), axis=0)
            return avg_cpc_vec

    __instance = __impl(cpc_list_file, cpc_vecs_file)

    def __getattr__(self, attr):
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        return setattr(self.__instance, attr, value)

    def __getitem__(self, key):
        return self.__instance.__getitem__(key)


class SIFTextVectorizer:

    """Implements a singleton pattern:
    Python Cookbook by David Ascher; Alex Martelli
    """
    
    class __impl:
        def __init__(self, json_vocab_file, ann_vecs_file, word_freq_file):
            self.alpha = 0.015
            self.vocab = json.load(open(json_vocab_file, 'r'))
            self.lut = {cpc:i for (i, cpc) in enumerate(self.vocab)}
            self.vecs = np.load(ann_vecs_file)
            self.dims = self.vecs.shape[1]
            self.dfs = json.load(open(word_freq_file, 'r'))
            self.sifs = [self.df2sif(self.dfs[w]) if w in self.dfs else 1.0
                            for w in self.vocab]
            self.gray = 0.00001 * np.ones(self.dims)

        def __getitem__(self, word):
            if word not in self.lut:
                return np.zeros(self.dims)
            i = self.lut[word]
            return self.vecs[i]

        def df2sif (self, df):
            """Calculate SIF from document frequency.

            SIF stands for smooth inverse frequency. It is high
            (nearly 1.0) for rare words and low for common words like
            like 'the' and 'of'.
            
            Args:
                freq (int): Document frequency of the word.
            
            Returns:
                float: Word SIF in range (0.0, 1.0)
            """
            df_max = self.dfs['the'] + 1
            proba = df / df_max
            return self.alpha / (self.alpha + proba)

        def tokenize (self, text):
            """Break a text into words.

            The text is transformed into lowercase and then all sequence
            of alphanumeric characters are returned.
            
            Args:
                text (str): Text to be tokenized
            
            Returns:
                list: Words in lowercase
            """
            words = re.findall(r'\w+', text.lower())
            return words if words is not None else []

        def embed (self, text, unique=True, remove_pc=False, average=False):
            """Return a vector representation of text.
            
            Args:
                text (str): English language text, typically a sentence
                unique (bool, optional): flag instructing the algorithm to drop
                    multiple occurrences of a word and consider it as one word
            
            Returns:
                numpy.ndarray: One-dimensional representation of the text
            """
            words = self.tokenize(text)
            if len(words) is 0:
                return self.gray
            if unique:
                words = list(set(words))
            idxs = [self.lut[w] for w in words if w in self.lut]
            if len(idxs) is 0:
                return self.gray
            if not average:
                matrix = np.array([self.vecs[i]*self.sifs[i] for i in idxs])
            else:
                matrix = np.array([self.vecs[i] for i in idxs])
            if remove_pc:
                matrix = self.remove_first_pc(matrix) 
            vec = np.average(matrix, axis=0)
            return vec

        def remove_first_pc (self, X):
            """Remove first principal component.
            
            Args:
                X (numpy.ndarray): Array of shape (n_vectors, n_dims)
            
            Returns:
                numpy.ndarray: Array of shape (n_vectors, n_dims)
            """
            svd = TruncatedSVD(n_components=1, n_iter=7, random_state=0)
            svd.fit(X)
            pc = svd.components_
            X = (X - X.dot(pc.transpose()) * pc)
            return X

    __instance = __impl(word_list_file, word_vecs_file, word_freq_file)

    def __getattr__(self, attr):
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        return setattr(self.__instance, attr, value)

    def __getitem__(self, key):
        return self.__instance.__getitem__(key)



def vectorize (item):
    """Return a vector representation of a patent, cpc code, or text.

    Checks whether the item is a patent number, a cpc code, a
    textual string (e.g., query) or a patent data dictionary.
    Depending on the type, it routes the item to an item-specific
    vectorizing function, e.g., `pn2vec`, `patent2vec`
    
    Args:
        item (str or dict): A cpc code, a patent number, a patent data dict,
            or a piece of text.
    
    Returns:
        numpy.ndarray: A one-dimensional vector.
    """
    if is_cpc_code(item):
        return CPCVectorizer()[item]
    
    elif is_patent_number(item):
        return pn2vec(item, use_cpcs=False)
    
    elif isinstance(item, dict):
        if 'abstract' in item and 'cpcs' in item:
            return patent2vec(item, use_cpcs=False)
    
    elif isinstance(item, str):
        return DistilBERTVectorizer().embed(item)

    else:
        return None


def pn2vec (pn, use_cpcs=True):
    """Return vector representation of a patent given its patent number.
    
    Args:
        pn (str): Patent number, e.g., US10112730B2 (patent number must
            have a kind code at the end)
    
    Returns:
        numpy.ndarray: One-dimensional vector representation of patent,
            `None` when patent number is not found in the database
    """
    patent_data = get_patent_data(pn)
    return patent2vec(patent_data, use_cpcs)


def patent2vec (patent, use_cpcs=True):
    """Return a vector representation of patent on the basis of its
        abstract and CPCs.
    
    Args:
        patent (dict): Patent data as a dictionary.
            Must two fields: `abstract` and `cpcs`. The former must be
            a string and the latter an array.
        use_cpcs (bool, optional): Whether to append an average CPC
            vector
    
    Returns:
        numpy.ndarray: One-dimensional vector representation of patent. 
    """
    if type(patent) is not dict:
        return None
    
    if 'abstract' not in patent: return None
    if type(patent['abstract']) is not str: return None
    text = patent['abstract']
    text_vec = vectorize(text)

    if use_cpcs is False:
        return text_vec
    else:
        if 'cpcs' not in patent: return None
        if type(patent['cpcs']) is not list: return None
        cpcs = patent['cpcs']
        vectorizer = CPCVectorizer()
        cpc_vec = vectorizer.embed(cpcs)
        return np.concatenate((text_vec, cpc_vec))
