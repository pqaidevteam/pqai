
from core.gf import is_class_code, is_patent_number
from config.config import models_dir

""" Initialize variables for cpc vectorizer """
cpc_vocab_file = 'cpc_vectors_256d.items.json'
cpc_vocab_file_path = models_dir + cpc_vocab_file


def vectorize (item):
	if is_cpc_code(item):
		return cpc2vec(item)
	elif is_patent_number(item):
		return pn2vec(item)
	elif isinstance(item, dict):
		if 'abstract' in item and 'cpcs' in item:
			return patent2vec(item)
	elif isinstance(item, str):
		return text2vec()


def cpc2vec (cpc_code):
	pass


def pn2vec (pn):
	pass


def patent2vec (patent_data):
	pass


def text2vec (text):
	pass