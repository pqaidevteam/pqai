import re
import json
import numpy as np

from config.config import models_dir
import core.gf
from core.gf import is_generic
from core.vectorizer import SIFTextVectorizer

embed = SIFTextVectorizer().__getitem__

dictionary = json.load(open(models_dir + 'glove-dictionary.json'))
l_vocab = json.load(open(models_dir + 'glove-vocab.lemmas.json'))
l_variations = json.load(open(models_dir + 'glove-dictionary.variations.json'))

def variations(word):
	if not word in dictionary:
		return [word]
	else:
		lemma = l_vocab[dictionary[word]]
		return l_variations[lemma]


def highlight(query, text):
	words = list(set(re.findall(r'[a-z]+', query.lower())))
	terms = list(set(re.findall(r'[a-z]+', text.lower())))

	words = [word for word in words if not is_generic(word)]
	terms = [term for term in terms if not is_generic(term)]

	qvecs = [embed(word) for word in words]
	tvecs = [embed(term) for term in terms]
	
	qvecs = qvecs / np.linalg.norm(qvecs, ord=2, axis=1, keepdims=True)
	tvecs = tvecs / np.linalg.norm(tvecs, ord=2, axis=1, keepdims=True)

	sims = np.matmul(qvecs, tvecs.transpose())
	to_highlight = []
	for i in range(sims.shape[0]):
		j = np.argmax(sims[i])
		if sims[i][j] > 0.6:
			to_highlight.append(terms[j])

	replacement = '<dGn9zx>\\1</dGn9zx>'
	for term in to_highlight:
		pattern = r'\b(' + term + r')\b'
		text = re.sub(pattern, replacement, text, count=1, flags=re.IGNORECASE)

	while True:
		flag = False
		matches = re.findall(r'([a-z]+)\s\<dGn9zx\>', text, re.IGNORECASE)
		for match in matches:
			if not is_generic(match.lower()):
				flag = True
				pattern = match + ' <dGn9zx>'
				replacement = '<dGn9zx>' + match + ' '
				text = re.sub(pattern, replacement, text, count=1, flags=re.IGNORECASE)
		if not flag:
			break

	while True:
		flag = False
		matches = re.findall(r'\<\/dGn9zx\>\s([a-z]+)', text, re.IGNORECASE)
		for match in matches:
			if not is_generic(match.lower()):
				flag = True
				pattern =  '</dGn9zx> ' + match
				replacement =  ' ' + match + '</dGn9zx>'
				text = re.sub(pattern, replacement, text, count=1, flags=re.IGNORECASE)
		if not flag:
			break

	pattern = r'dGn9zx'
	replacement = 'strong'
	text = re.sub(pattern, replacement, text)
	return (text, to_highlight)