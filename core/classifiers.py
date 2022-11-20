"""
    Classifiers: they associate one of a finite number of categorical variables
    to a given text

    Subclass predictors are a special type of classifiers.
    They associate one of the 600+ CPC/IPC subclasses to a given text snippet.
    They may be used to identify the technology area of, for example, a query
    manually written by a user for prior-art searching. This information
    can then subsequently be used to narrow down part(s) of a database where
    search is actually done.
"""

from pathlib import Path
import json
import re
import numpy as np
from keras.models import model_from_json
from keras_bert import get_custom_objects, Tokenizer

BASE_DIR = str(Path(__file__).parent.parent.resolve())
MODELS_DIR = f"{BASE_DIR}/models"


class Singleton(type):

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class BOWSubclassPredictor(metaclass=Singleton):

    """A bag of word-vectors based neural network for associating subclasses
    with snippets of text
    """

    def __init__(self):
        self.model_file = f"{MODELS_DIR}/pmbl2subclass.json"
        self.weights_file = f"{MODELS_DIR}/pmbl2subclass.h5"
        self.features_file = f"{MODELS_DIR}/pmbl2subclass.features.json"
        self.targets_file = f"{MODELS_DIR}/pmbl2subclass.targets.json"

        # These variables are initialized by `_load_in_memory ()` when
        # first request for prediction is received
        self.model = None
        self.features = None
        self.features_dict = None
        self.targets = None
        self.targets_dict = None

    def _load_in_memory(self):
        """Load the Keras model, features and target names in memory."""
        self._load_model()
        self._load_features()
        self._load_targets()

    def _load_model(self):
        """Load the Keras model into main memory"""
        with open(self.model_file, "r") as file:
            self.model = model_from_json(file.read())
            self.model.load_weights(self.weights_file)

    def _load_features(self):
        """Load the features (words) into memory"""
        with open(self.features_file, "r") as file:
            self.features = json.loads(file.read())
            self.features_dict = {f: i for i, f in enumerate(self.features)}

    def _load_targets(self):
        """Load targets (subclass codes) into memory"""
        with open(self.targets_file, "r") as file:
            self.targets = json.loads(file.read())
            self.targets_dict = {t: i for i, t in enumerate(self.targets)}

    def _to_feature_vector(self, text):
        """Get a one-hot encoded vector for the given text snippet.

        Args:
            text (str): Text to be encoded.

        Returns:
            numpy.ndarray: A one-dimensional one-hot encoded vector.
        """
        tokens = self._tokenize(text)
        vector = np.zeros(len(self.features_dict), dtype=np.uint8)

        # Create one-hot vector representation
        for token in tokens:
            if not token in self.features_dict:
                continue
            i = self.features_dict[token]
            vector[i] = 1
        return vector

    @staticmethod
    def _tokenize(text):
        """Get tokens (words) from given text."""
        return re.findall(r"\b[a-z]+\b", text.lower())

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


class BERTSubclassPredictor(metaclass=Singleton):

    """Singleton class for predicting subclass for a given piece of text
    using a model obtained by fine-tuning BERT
    """

    MODEL_PATH = f"{MODELS_DIR}/uncased_L-12_H-768_A-12"

    def __init__(self):
        self.vocab_file = f"{self.MODEL_PATH}/vocab.txt"
        self.model_file = f"{self.MODEL_PATH}/cpcs_classify.json"
        self.weights_file = f"{self.MODEL_PATH}/cpcs_classify.h5"
        self.targets_file = f"{self.MODEL_PATH}/cpcs_classify.targets.txt"
        self.seq_len = 128

        # The following variables are lazy-loaded. They are initialized
        # when first request for prediction is received
        self.model = None
        self.subclass_codes = []  # valid subclass weights
        self.tokens_dict = {}

    def _load_in_memory(self):
        """Load the Keras model, features, and targets in memory"""
        self._load_model()
        self._load_subclass_codes()
        self._load_dictionary()

    def _load_model(self):
        """Load the Keras model in memory for inference"""
        with open(self.model_file, "r") as file:
            self.model = model_from_json(
                file.read(), custom_objects=get_custom_objects()
            )
            self.model.load_weights(self.weights_file)

    def _load_subclass_codes(self):
        """Load a list of valid subclasses into the memory"""
        with open(self.targets_file, "r") as file:
            self.subclass_codes = file.read().strip().splitlines()

    def _load_dictionary(self):
        """Load the mapping of tokens to indexes into the memory"""
        with open(self.vocab_file) as f:
            tokens = f.read().strip().splitlines()
            self.tokens_dict = {token: i for i, token in enumerate(tokens)}

    def _to_feature_vector(self, text):
        """Get encoded vector for the given text snippet.

        Args:
            text (str): Text to be encoded.

        Returns:
            numpy.ndarray: A pair of one-dimensional encoded vector with
                segments.
        """
        tokenizer = Tokenizer(self.tokens_dict)
        tokens, segments = tokenizer.encode(first=text, max_len=self.seq_len)
        tokens_encoded = np.array(tokens).reshape(1, self.seq_len)
        segments_encoded = np.array(segments).reshape(1, self.seq_len)
        return [tokens_encoded, segments_encoded]

    def predict_subclasses(self, text, n=5, limit_to=None):
        """Find relevant CPC technology subclasses for a given text snippet.

        Args:
            text (str): Input text
            n (int): No. of predictions
            limit_to (list): Return from only among these subclasses

        Returns:
            list: Array of subclass codes, most relevant first.
        """
        if not self.model:
            self._load_in_memory()

        x = self._to_feature_vector(text)
        y = self.model.predict_step(x)[0]

        # sort subclasses in descending order of relevancy
        subclasses = [self.subclass_codes[i] for i in np.argsort(y)[::-1]]

        if limit_to:
            subclasses = [c for c in subclasses if c in limit_to]

        return subclasses[:n]
