import numpy as np
import json
import re

from core.gf import is_class_code, is_patent_number
from config.config import models_dir
from core.db import get_patent_data

def freq2coef(freq):
    """Calculate word weight given its document frequency.

    Word weight is high (nearly 1.0) for rare words and low for
    common words like 'the' and 'of'.
    
    Args:
        freq (int): Document frequency of the word.
    
    Returns:
        float: Word weight in range (0.0, 1.0)
    """
    a = 0.015
    n = freq
    N = word_freq['the'] + 1
    p = n / N
    return a/(a+p)


# Variables used for cpc vectorization
cpc_list_file = models_dir + 'cpc_vectors_256d.items.json'
cpc_vecs_file = models_dir + 'cpc_vectors_256d.npy'
cpc_vecs = None
cpc_dims = None
cpc_list = None
cpc_dict = None


# Variables used for text vectorization
word_vecs_file = models_dir + 'glove-We.npy'
word_list_file = models_dir + 'glove-We.npy'
word_freq_file = models_dir + 'dfs.json'
word_vecs = None
word_list = None
word_dims = None
word_dict = None
word_freq = None
word_coef = None


def init_cpc_vecs():
    """Read cpc vectors and cpc codes from the disk. Initialize other
        variables used for cpc vectorization.
    """
    global cpc_vecs
    global cpc_dims
    global cpc_list
    global cpc_dict
    cpc_vecs = np.load(cpc_vecs_file)
    cpc_dims = cpc_vecs.shape[1]
    cpc_list = json.load(open(cpc_list_file, 'r'))
    cpc_dict = {cpc:i for (i, cpc) in enumerate(cpc_list)}


def init_word_vecs():
    """Read word list and word vectors codes from disk. Initialize other
        variables used for text vectorization.
    """
    global word_vecs
    global word_dims
    global word_list
    global word_dict
    word_vecs = np.load(word_vecs_file)
    word_dims = word_vecs.shape[1]
    word_list = json.load(open(word_list_file, 'r'))
    word_dict = {word:i for (i, word) in enumerate(word_list)}
    word_freq = json.load(open(word_freq_file, 'r'))
    word_coef = [freq2coef(word_freq[w]) if w in word_freq else 1.0
                    for w in word_list]


def vectorize (item):
    """Return a vector representation of a patent, cpc code, or text.

    Checks whether the item is a patent number, a cpc code, a
    textual string (e.g., query) or a patent data dictionary.
    Depending on the type, it routes the item to an item-specific
    vectorizing functions from among these:
    `cpc2vec`, `pn2vec`, `patent2vec`, `text2vec`
    
    Args:
        item (str or dict): A cpc code, a patent number, a patent data dict,
            or a piece of text.
    
    Returns:
        numpy.ndarray: A one-dimensional vector.
    """
    if is_cpc_code(item):
        return cpc2vec(item)
    
    elif is_patent_number(item):
        return pn2vec(item)
    
    elif isinstance(item, dict):
        if 'abstract' in item and 'cpcs' in item:
            return patent2vec(item)
    
    elif isinstance(item, str):
        return text2vec()


def cpc2vec (cpc_code, strict=False):
    """Return vector representation of a cpc class.
    
    Args:
        cpc_code (str): CPC code, e.g. H04W72/02
        strict (bool, optional): If `True`, return `None` for unknown
            CPC codes, if `False` return a zero-vector.
    
    Returns:
        numpy.ndarray: One-dimensional vector representation of CPC
    """
    init_cpc_vecs() if cpc_vecs is None else None
    if cpc_code not in cpc_dict:
        return np.zeros(cpc_dims) if not strict else None 
    i = cpc_dict[cpc_code]
    return cpc_vecs[i]


def pn2vec (pn):
    """Return vector representation of a patent given its patent number.
    
    Args:
        pn (str): Patent number, e.g., US10112730B2 (patent number must
            have a kind code at the end)
    
    Returns:
        numpy.ndarray: One-dimensional vector representation of patent,
            `None` when patent number is not found in the database
    """
    patent_data = get_patent_data(pn)
    return patent2vec(patent_data)


def patent2vec (patent_data):
    """Return a vector representation of patent on the basis of its
        abstract and CPCs.
    
    Args:
        patent_data (dict): Patent data in the form of a dictionary.
            Must two fields: `abstract` and `cpcs`. The former must be
            a string and the latter an array.
    
    Returns:
        numpy.ndarray: One-dimenstional vector representation of patent.
    """
    if 'abstract' not in patent_data or 'cpcs' not in patent_data:
        return None
    
    text = patent_data['abstract']
    cpcs = patent_data['cpcs']
    if not isinstance(text, str) or not isinstance(cpcs, list):
        return None

    text_vec = text2vec(text)
    
    cpc_vecs = [cpc2vec(cpc) for cpc in cpcs]
    avg_cpc_vec = np.average(np.array(cpc_vecs), axis=0)
    
    return np.concatenate((text_vec, avg_cpc_vec))


def text2vec (text, unique=False):
    """Summary
    
    Args:
        text (TYPE): Description
        unique (bool, optional): Description
    
    Returns:
        TYPE: Description
    """
    words = tokenize(text)
    words = [w for w in words if w in word_dict]
    if unique:
        words = list(set(words))
    x = [word_dict[w] for w in words]
    if len(x) == 0:
        return np.array([0.00001]*word_dims)
    vec = compose(x, We, Ww)
    return vec
    