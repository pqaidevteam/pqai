from os.path import join
import numpy as np
import json
import re
import codecs

from config.config import models_dir
from core.utils import tokenize

class BOWSubclassPredictor:

    """Singleton class for predicting subclass for a given piece of text
       using a bag of words vectors-based neural network
    """
    
    class __impl:
    
        def __init__(self):
            self.model_file = join(models_dir, 'pmbl2subclass.json')
            self.weights_file = join(models_dir, 'pmbl2subclass.h5')
            self.features_file = join(models_dir, 'pmbl2subclass.features.json')
            self.targets_file = join(models_dir, 'pmbl2subclass.targets.json')

            # These variables are initialized by `_load_in_memory ()` when
            # first request for prediction is received
            self.model = None
            self.features = None
            self.features_dict = None
            self.targets = None
            self.targets_dict = None

        def _load_in_memory (self):
            """Load the Keras model, features and target names in memory.
            """
            self._load_model()
            self._load_features()
            self._load_targets()

        def _load_model (self):
            """Load the Keras model into main memory
            """
            from keras.models import model_from_json

            # Load Keras model architecture from json and weights from h5 file
            with open(self.model_file, 'r') as file:
                self.model = model_from_json(file.read())
                self.model.load_weights(self.weights_file)

        def _load_features (self):
            """Load the features (words) into memory
            """
            with open(self.features_file, 'r') as file:
                self.features = json.loads(file.read())
                self.features_dict = {f:i for i,f in enumerate(self.features)}

        def _load_targets (self):
            """Load targets (subclass codes) into memory
            """
            with open(self.targets_file, 'r') as file:
                self.targets = json.loads(file.read())
                self.targets_dict = {t:i for i,t in enumerate(self.targets)}

        def _to_feature_vector (self, text):
            """Get a one-hot encoded vector for the given text snippet.
            
            Args:
                text (str): Text to be encoded.
            
            Returns:
                numpy.ndarray: A one-dimensional one-hot encoded vector.
            """
            tokens = tokenize(text, lowercase=True, alphanums=False)
            vector = np.zeros(len(self.features_dict), dtype=np.uint8)

            # Create one-hot vector representation
            for token in tokens:
                if not token in self.features_dict:
                    continue
                i = self.features_dict[token]
                vector[i] = 1
            return vector


        def predict_subclasses(self, text, n=5, limit_to=None):
            """Find relevant CPC technology subclasses for a given text snippet. 
            
            Args:
                text (str): Input text.
                n (int, optional): Number of subclasses to return.
                limit_to (list, optional): Predict subclasses only from the given
                    list (intended for cases when you want to limit prediction
                    to a specific set of classes)
            
            Returns:
                list: Array of subclass codes, most relevant first.
            """
            if not self.model:
                self._load_in_memory()
            x = self._to_feature_vector(text)

            y_pred = self.model.predict(np.array([x]))[0]

            # sort subclasses in descending order of relevancy
            subclasses = [self.targets[i] for i in np.argsort(y_pred)[::-1]]

            if limit_to:
                subclasses = [c for c in subclasses if c in limit_to]

            # return top-n
            return subclasses[:n]

    __instance = __impl()

    def __getattr__(self, attr):
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        return setattr(self.__instance, attr, value)

    def __getitem__(self, key):
        return self.__instance.__getitem__(key)


class BERTSubclassPredictor:

    """Singleton class for predicting subclass for a given piece of text
       using a model obtained by fine-tuning BERT
    """
    
    class __impl:

        def __init__(self):
            self.pretrained_path = join(models_dir, 'uncased_L-12_H-768_A-12')
            self.vocab_file = join(self.pretrained_path, 'vocab.txt')
            self.model_file = join(self.pretrained_path, 'cpcs_classify.json')
            self.weights_file = join(self.pretrained_path, 'cpcs_classify.h5')
            self.targets_file = join(self.pretrained_path, 'cpcs_classify.targets.txt')
            self.SEQ_LEN = 128

            # The following variables are lazy-loaded. They are initialized
            # when first request for prediction is received
            self.model = None
            self.subclass_codes = [] # valid subclass weights
            self.tokens_dict = {}

        def _load_in_memory(self):
            """Load the Keras model, features, and targets in memory
            """
            self._load_model()
            self._load_subclass_codes()
            self._load_dictionary()

        def _load_model(self):
            """Load the Keras model in memory for inference
            """
            import codecs
            from keras.models import model_from_json
            from keras_bert import get_custom_objects

            with open(self.model_file, 'r') as file:
                self.model = model_from_json( file.read(),
                                              custom_objects=get_custom_objects())
                self.model.load_weights(self.weights_file)
        
        def _load_subclass_codes(self):                  
            """Load a list of valid subclasses into the memory
            """
            with open(self.targets_file, 'r') as file:
                self.subclass_codes = file.read().strip().splitlines()

        def _load_dictionary(self):
            """Load the mapping of tokens to indexes into the memory
            """
            with codecs.open(self.vocab_file, 'r', 'utf8') as reader:
                for line in reader:
                    token = line.strip()
                    self.tokens_dict[token] = len(self.tokens_dict)

        def _to_feature_vector (self, text):
            """Get encoded vector for the given text snippet.
           
            Args:
                text (str): Text to be encoded.
           
            Returns:
                numpy.ndarray: A pair of one-dimensional encoded vector with
                    segments.
            """
            from keras_bert import Tokenizer
            tokenizer = Tokenizer(self.tokens_dict)
            tokens, segments = tokenizer.encode(first=text, max_len=self.SEQ_LEN)
            tokens_encoded = np.array(tokens).reshape(1, self.SEQ_LEN)
            segments_encoded = np.array(segments).reshape(1, self.SEQ_LEN)
            return [tokens_encoded, segments_encoded]

        def predict_subclasses (self, text):
            """Find relevant CPC technology subclasses for a given text snippet.
            
            Args:
                text (str): Input text.
            
            Returns:
                list: Array of subclass codes, most relevant first.
            """
            if not self.model:
                self._load_in_memory()
            
            x = self._to_feature_vector(text)
            y = self.model.predict_step(x)[0]

            # sort subclasses in descending order of relevancy
            subclasses = [self.subclass_codes[i] for i in np.argsort(y)[::-1]]
            return subclasses

    __instance = __impl()

    def __getattr__(self, attr):
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        return setattr(self.__instance, attr, value)

    def __getitem__(self, key):
        return self.__instance.__getitem__(key)