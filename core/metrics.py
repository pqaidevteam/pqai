from wmd import WMD
import numpy as np
import json

from core.utils import tokenize
from config.config import models_dir

class WordMoverDistance:

    """Summary
    """
    
    def __init__(self, ignore_stopwords=True):
        self.stopword_filter_on = ignore_stopwords
        self._tokenize = tokenize
        self._dictionary = self._load_dictionary()
        self._embeddings = self._load_embeddings()
        self._stopwords = set(self._load_stopwords())

    def calculate (self, text_a, text_b):
        """Summary
        
        Args:
            text_a (TYPE): Description
            text_b (TYPE): Description
        """
        tokens_a = self._preprocess(text_a)
        tokens_b = self._preprocess(text_b)
        nbow = {
                    "text_a": self._preprocess(text_a),
                    "text_b": self._preprocess(text_b)
                }
        calc = WMD(self._embeddings, nbow, vocabulary_min=1)
        distance = calc.nearest_neighbors("text_a")[0][1]
        return distance

    def _preprocess(self, text):
        """Summary
        
        Args:
            text (TYPE): Description
        
        Returns:
            TYPE: Description
        """
        tokens = self._tokenize(text)
        indexes = [self._dictionary[t] for t in tokens if t in self._dictionary]
        weights = [0.0 if (t in self._stopwords
                    and self.stopword_filter_on) else 1.0
                    for t in tokens]
        return (text, indexes, np.array(weights, dtype='float32'))


        return 

    def _load_dictionary(self):
        """Summary
        
        Returns:
            TYPE: Description
        
        Raises:
            Exception: Description
        """
        dict_file = models_dir + 'glove-dictionary.json'
        try:
            file = open(dict_file, 'r')
        except:
            raise Exception('Unable to read dictionary file.')
        
        try:
            dictionary = json.load(file)
        except:
            raise Exception('Could not parse dictionary file.')
        
        file.close()
        return dictionary

    def _load_embeddings(self):
        """Summary
        
        Returns:
            TYPE: Description
        
        Raises:
            Exception: Description
        """
        emb_file = models_dir + 'glove-We.npy'
        try:
            embeddings = np.load(emb_file)
            return embeddings.astype('float32')
        except:
            raise Exception('Unable to read embeddings file.')

    def _load_stopwords(self):
        """Summary
        
        Returns:
            TYPE: Description
        
        Raises:
            Exception: Description
        """
        stopwords_file = models_dir + 'stopwords.txt'
        try:
            file = open(stopwords_file, 'r')
        except:
            raise Exception('Error in reading stopwords file.')

        stopwords = file.read().strip().splitlines()
        file.close()
        return stopwords