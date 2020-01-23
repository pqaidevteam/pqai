import numpy as np
import re
import json

from config.config import models_dir
from core.gf import tokenize

model_file = models_dir + 'pmbl2subclass.json'
weights_file = models_dir + 'pmbl2subclass.h5'
features_file = models_dir + 'pmbl2subclass.features.json'
targets_file = models_dir + 'pmbl2subclass.targets.json'

# Global variables, initialized by `load_model()` when first request for
# prediction is received by `predict_subclasses()`
loaded_model = None
features = None
features_dict = None
targets = None
targets_dict = None

def load_model():
	"""Load the keras model, features and target names in memory.
	"""
	global loaded_model
	global features
	global features_dict
	global targets
	global targets_dict

	from keras.models import model_from_json

	# Load Keras model architecture from json and weights from h5 file
	with open(model_file, 'r') as file:
		loaded_model = model_from_json(file.read())
		loaded_model.load_weights(weights_file)

	# Load features (words)
	with open(features_file, 'r') as file:
		features = json.loads(file.read())
		features_dict = {feat:i for i, feat in enumerate(features)}

	# Load targets (subclass codes)
	with open(targets_file, 'r') as file:
		targets = json.loads(file.read())
		targets_dict = {tgt:i for i, tgt in enumerate(targets)}


def to_feature_vector (text, dictionary):
    """Get a one-hot encoded vector for the given text snippet.
    
    Args:
        text (str): Text to be encoded.
        dictionary (dict): Dictionary with words as keys and their
        	positions in the vector as values.
        	Example:
        	{ 'the': 0, 'of': 1, 'a': 2, ..., 'zirconium': 11234}
    
    Returns:
        numpy.ndarray: A one-dimensional one-hot encoded vector.
    """
    tokens = tokenize(text, lowercase=True, alphanums=False)
    vector = np.zeros(len(dictionary), dtype=np.uint8)
    for token in tokens:
        if not token in dictionary:
            continue
        i = dictionary[token]
        vector[i] = 1
    return vector


def predict_subclasses (text, n=5):
	"""Find relevant CPC technology subclasses for a given text snippet. 
	
	Args:
	    text (str): Input text.
	    n (int, optional): Number of subclasses to return.
	
	Returns:
	    list: Array of subclass codes, most relevant first.
	"""
	if not loaded_model:
		load_model()
	x = to_feature_vector(text, features_dict)
	y_pred = loaded_model.predict(np.array([x]))[0]
	subclasses = [targets[i] for i in np.argsort(y_pred)[::-1][:5]]
	return subclasses
