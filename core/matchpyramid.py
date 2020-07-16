import re
import types
from matchzoo.preprocessors import BasicPreprocessor
from matchzoo.engine.base_preprocessor import load_preprocessor
from matchzoo.engine.base_model import load_model
from matchzoo.preprocessors.chain_transform import chain_transform
import numpy as np
from config.config import models_dir

MAX_LEN = 200
MODEL_DIR = f'{models_dir}MatchPyramid_200_tokens/'
preprocessor = load_preprocessor(f"{MODEL_DIR}/preprocessor")
model = load_model(f"{MODEL_DIR}model")

"""
	Set embeddings for the <pad> and <oov> terms
	to zero vectors so that they have zero interaction
	among themselves and with other terms.
"""
M = model.get_embedding_layer().get_weights()[0]
M[0] = np.zeros(256)
M[1] = np.zeros(256)
model.get_embedding_layer().set_weights([M])


def get_d_pool_array(n_docs, MAX_LEN):
	d_pool_list = []
	for i in range(MAX_LEN):
		temp_list = []
		for j in range(MAX_LEN):
			temp_list.append([i,j])
		d_pool_list.append(temp_list)
	
	arr = []
	for i in range(n_docs):
		arr.append(d_pool_list)
	d_pool_array = np.asarray(arr)
	
	del d_pool_list
	del arr
	
	return d_pool_array

class CustomTokenize():
	def transform(self, input_: str) -> list:
		return re.findall(r'\w+', input_)
	

def get_transformer(preprocessor: BasicPreprocessor, mode: str)\
		-> types.FunctionType:
	transformer_units = preprocessor._units[:]
	if mode == 'right':
		transformer_units.append(preprocessor._context['filter_unit'])
	
	transformer_units.append(preprocessor._context['vocab_unit'])
	if mode == 'right':
		transformer_units.append(preprocessor._right_fixedlength_unit)
	else:
		transformer_units.append(preprocessor._left_fixedlength_unit)
	transformer = chain_transform(transformer_units)
	return transformer

transformer_left = get_transformer(preprocessor, 'left')
transformer_right = get_transformer(preprocessor, 'right')

def get_similarity_scores(texts_left, texts_right):
	inputs_left = [transformer_left(text) for text in texts_left]
	inputs_right = [transformer_right(text) for text in texts_right]
	output = model.predict([inputs_left, inputs_right, get_d_pool_array(1, MAX_LEN)])[0]
	return output

def calculate_similarity(left_val, right_val):
	if isinstance(left_val, str) and isinstance(right_val, str):
		return get_similarity_scores([left_val], [right_val])[0]
	elif isinstance(left_val, str) and isinstance(right_val, list):
		n = len(right_val)
		return get_similarity_scores([left_val]*n, right_val)
	elif isinstance(left_val, list) and isinstance(right_val, list):
		if len(left_val) == len(right_val):
			return get_similarity_scores(left_val, right_val)
		else:
			return None
	else:
		return None