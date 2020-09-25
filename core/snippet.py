import numpy as np
from random import randrange
import re
from core import utils
from core.highlighter import highlight as highlighter_fn

from core.vectorizer import SIFTextVectorizer
encoder_fn = SIFTextVectorizer().embed


from core.reranking import CustomRanker
ranker = CustomRanker()


def last_few_words(sent):
    num_words = randrange(5, 10)
    i = len(sent)-1
    n = 0
    while i > 0 and n < num_words:
        if sent[i] == ' ':
            n += 1
        i -= 1
    return '...' + sent[i+1:len(sent)] + ' '


def first_few_words(sent):
    num_words = randrange(2, 5)
    i = 0
    n = 0
    while i < len(sent) and n < num_words:
        if sent[i] == ' ':
            n += 1
        i += 1
    return ' ' + sent[0:i] + '...'

def extract_snippet(query, text, htl_on=True):
	sents = valid_sentences(text)
	idx = best_sent_for(query, sents)
	best_sent = sents[idx]

	before = last_few_words(sents[idx-1]) if idx > 0 else ''
	after = first_few_words(sents[idx+1]) if idx+1 < len(sents) else ''
	center = highlighter_fn(query, best_sent)[0] if htl_on else best_sent
	snippet = before + center + after
	return snippet


def best_sent_for_old_method(query, sents):
	words = list(set(re.findall(r'[a-z]+', query.lower())))
	words = [word for word in words if not utils.is_generic(word)]
	qvecs = np.array([encoder_fn(word) for word in words])
	qvecs = qvecs / np.linalg.norm(qvecs, ord=2, axis=1, keepdims=True)

	sent_scores = np.zeros(len(sents))
	for s, sent in enumerate(sents):
		terms = list(set(re.findall(r'[a-z]+', sent.lower())))
		terms = [term for term in terms if not utils.is_generic(term)]
		tvecs = np.array([encoder_fn(term) for term in terms])
		
		# to handle the special case where all words in the
		# sentence are generic, e.g. the invention describes...
		if tvecs.shape[0] == 0:
			continue		# with zero score for this sentence

		# to handle the special case where the sentence
		# is shorter than the query
		# if tvecs.shape[0] < qvecs.shape[0]:
		# 	continue

		tvecs = tvecs / np.linalg.norm(tvecs, ord=2, axis=1, keepdims=True)

		sims = np.matmul(qvecs, tvecs.transpose())

		word_scores = np.zeros(sims.shape[0])
		for i in range(sims.shape[0]):
			word_score = np.max(sims[i])
			word_scores[i] = word_score

		# long sentences are likely to win in this scoring
		# simply because they have more words
		sent_len = sims.shape[1]
		penalty_factor = 1.0 if sent_len <= 20 else ((sent_len-20)**(-0.1))

		# the measure of 'goodness' of a sentence
		# could be replaced with a better thought out one
		sent_score = penalty_factor*word_scores.sum()
		sent_scores[s] = sent_score

	best_idx = np.argmax(sent_scores)
	terms = list(set(re.findall(r'[a-z]+', sents[best_idx].lower())))
	terms = [term for term in terms if not utils.is_generic(term)]
	return best_idx


def best_sent_for(query, sents):
	best_sent_idx = ranker.rank(query, sents)[0]
	return best_sent_idx


def valid_sentences(text):
	sents = utils.get_sentences(text)
	sents = [sent for sent in sents if len(sent) > 50]
	return sents


def map_elements_to_text (elements, target_text, encoder_fn):
    """Find sentences in target_text that are semantically most similar
        to claim elements.
    
    Args:
        elements (list): List of claim element strings (e.g. preamble)
        target_text (str): Text to which mapping is to be done, e.g.,
        	description of a patent reference.
        encoder_fn (method): The vectorizer function; it should accept
        	a list of strings and return a list of vectors, aka sentence
        	embedding function.
    
    Returns:
        list: list of dictionaries with keys `element`, `mapping`, and
        	`similarity`
    """
    element_vectors = np.array(encoder_fn(elements))

    target_sentences = utils.get_sentences(target_text)
    sent_vectors = np.array(encoder_fn(target_sentences))
    
    cosine_sims = np.dot(
    	utils.normalize_rows(element_vectors), utils.normalize_cols(sent_vectors.T))
    
    sent_idxs = cosine_sims.argmax(axis=1)
    mappings = []
    for i, element in enumerate(elements):
    	mapping = {}
    	j = sent_idxs[i]
    	mapping['element'] = element
    	mapping['mapping'] = target_sentences[j]
    	mapping['ctx_before'] = target_sentences[j-1] if j-1 > 0 else ''
    	mapping['ctx_after'] = target_sentences[j+1] if j+1 < len(target_sentences) else ''
    	mapping['similarity'] = float(cosine_sims[i][j])
    	mappings.append(mapping)
    return mappings