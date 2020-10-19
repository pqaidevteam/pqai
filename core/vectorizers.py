import re
import numpy as np
import json
from sklearn.decomposition import TruncatedSVD
from sentence_transformers import SentenceTransformer

from core.encoders import Encoder

from config.config import models_dir

class Vectorizer(Encoder):

    def __init__(self):
        super().__init__()
        self._name = 'Vectorizer'

    def _input_validation_fn(self, item):
        return isinstance(item, str)

    def _encoding_fn(self, item):
        return embed(item)

    def embed(self, item):
        pass


class SentBERTVectorizer:

    class __impl(Vectorizer):

        sentbert_model_path = models_dir + 'vectorizer_distilbert_poc/'
        
        def __init__(self):
            super().__init__()
            self._name = 'SentBERTVectorizer'
            self._model = None # Lazy loads

        def load (self):
            self._model = SentenceTransformer(self.sentbert_model_path)

        def embed (self, text):
            self._load_if_needed()
            vec = self._model.encode([text])[0]
            return vec

        def encode_many (self, texts):
            self._load_if_needed()
            vecs = np.array(self._model.encode(texts))
            return vecs

        def _load_if_needed(self):
            if self._model is None:
                self.load()

    __instance = __impl()

    def __getattr__(self, attr):
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        return setattr(self.__instance, attr, value)

    def __getitem__(self, key):
        return self.__instance.__getitem__(key)


class CPCVectorizer:
    
    class __impl(Vectorizer):

        cpc_list_file = models_dir + 'cpc_vectors_256d.items.json'
        cpc_vecs_file = models_dir + 'cpc_vectors_256d.npy'
        
        def __init__(self):
            super().__init__()
            self._name = 'CPCVectorizer'
            with open(self.cpc_list_file) as file:
                self.vocab = json.load(file)
            self.lut = {cpc:i for (i, cpc) in enumerate(self.vocab)}
            self.vecs = np.load(self.cpc_vecs_file)
            self.dims = self.vecs.shape[1]
            self.gray = 0.00001 * np.ones(self.dims)

        def __getitem__(self, cpc_code):
            if cpc_code not in self.lut:
                return np.zeros(self.dims) 
            i = self.lut[cpc_code]
            return self.vecs[i]

        def embed (self, cpcs):
            if not [cpc for cpc in cpcs if cpc in self.lut]:
                return self.gray
            cpc_vecs = [self[cpc] for cpc in cpcs if cpc in self.lut]
            avg_cpc_vec = np.average(np.array(cpc_vecs), axis=0)
            return avg_cpc_vec

    __instance = __impl()

    def __getattr__(self, attr):
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        return setattr(self.__instance, attr, value)

    def __getitem__(self, key):
        return self.__instance.__getitem__(key)


class SIFTextVectorizer:
    
    class __impl(Vectorizer):
        
        word_vecs_file = models_dir + 'glove-We.npy'
        word_list_file = models_dir + 'glove-vocab.json'
        word_freq_file = models_dir + 'dfs.json'
        
        def __init__(self):
            super().__init__()
            self._name = 'SIFTextVectorizer'

            self.alpha = 0.015
            self.vocab = self._read_json(self.word_list_file)
            self.dfs = self._read_json(self.word_freq_file)
            self.vecs = np.load(self.word_vecs_file)
            self.lut = self._lookup_table()
            self.sifs = [self._sif(w) for w in self.vocab]
            self.dims = self.vecs.shape[1]
            self.gray = 0.00001 * np.ones(self.dims)

        def _read_json(self, filepath):
            with open(filepath) as file:
                return json.load(file)

        def _lookup_table(self):
            return {cpc:i for (i, cpc) in enumerate(self.vocab)}

        def _sif (self, word):
            if not word in self.dfs:
                return 1.0
            df = self.dfs[word]
            df_max = self.dfs['the'] + 1
            proba = df / df_max
            return self.alpha / (self.alpha + proba)

        def __getitem__(self, word):
            if word not in self.lut:
                return np.zeros(self.dims)
            i = self.lut[word]
            return self.vecs[i]

        def tokenize (self, text):
            words = re.findall(r'\w+', text.lower())
            return words if words is not None else []

        def embed (self, text, unique=True, remove_pc=False, average=False):
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
            svd = TruncatedSVD(n_components=1, n_iter=7, random_state=0)
            svd.fit(X)
            pc = svd.components_
            X = (X - X.dot(pc.transpose()) * pc)
            return X

    __instance = __impl()

    def __getattr__(self, attr):
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        return setattr(self.__instance, attr, value)

    def __getitem__(self, key):
        return self.__instance.__getitem__(key)