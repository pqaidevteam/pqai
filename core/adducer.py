import numpy as np
import gf
from random import randrange
import re

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


def generate_snippet_(query, text, encoder_fn, highlighter=None):
	sents = gf.get_sentences(text)
	sents = [sent for sent in sents if len(sent) > 50]
	sent_vecs = encoder_fn(sents)
	# sent_vecs = sent_vecs / np.linalg.norm(sent_vecs, ord=2, axis=1, keepdims=True)
	
	query_vec = encoder_fn(query)
	# query_vec /= np.linalg.norm(query_vec)
	query_vec = query_vec.reshape(256, 1)
	
	sim_scores = np.matmul(sent_vecs, query_vec).flatten()

	# sort indexes in decreasing order of similarity
	idx_sorted = list(sim_scores.argsort()[::-1])
	
	denscending_scores = [sim_scores[i] for i in idx_sorted]

	n_max = 1   # no. of sentences to keep in the snippet
	
	
	query_words = re.findall(r'[a-z]+', query.lower())
	yet_to_find = re.findall(r'[a-z]+', query.lower())

	snippets = []
	while len(snippets)<n_max and len(idx_sorted) > 0 and len(yet_to_find) > 0:
		i = idx_sorted.pop(0)
		core_snippet = sents[i]
		if core_snippet[-1] == '.':  # a proper sentence
			if highlighter:
				hlt_sent, found = highlighter(query_words, sents[i])
				newfound = 0
				for word in found:
					if word in yet_to_find:
						yet_to_find.pop(yet_to_find.index(word))
						newfound += 1
				if (len(snippets) > 0 and newfound == 0):
					continue					
			else:
				hlt_sent = sents[i]
			snippet = '<span class="snippet">' + hlt_sent + '</span>'
			before = ''
			after = ''
			if i > 0:
				before = '...' + last_few_words(sents[i-1])
				before = '<span class="before">' + before + '</span>'
			if len(re.findall(r'\s+', snippet)) > 85:
				snippet = re.search(r'(\S+\s){,80}', snippet).group().strip()
				after = '...'
			elif i+1 < len(sents):
				after = first_few_words(sents[i+1]) + '...'
				after = '<span class="after">' + after + '</span>'
			snippet = ' '.join([before, snippet, after])
			snippets.append(snippet)
	full_snippet = '<br>'.join(snippets)
	return full_snippet


def generate_snippet(query, text, encoder_fn, highlighter=None):
	sents = valid_sentences(text)
	idx = best_sent_for(query, sents, encoder_fn)
	best_sent = sents[idx]

	before = last_few_words(sents[idx-1]) if idx > 0 else ''
	after = first_few_words(sents[idx+1]) if idx+1 < len(sents) else ''
	center, _ = highlighter(query, best_sent) if highlighter else best_sent

	snippet = before + center + after
	return snippet


def best_sent_for(query, sents, encoder_fn):
	words = list(set(re.findall(r'[a-z]+', query.lower())))
	words = [word for word in words if not gf.is_generic(word)]
	qvecs = np.array([encoder_fn(word) for word in words])
	qvecs = qvecs / np.linalg.norm(qvecs, ord=2, axis=1, keepdims=True)

	sent_scores = np.zeros(len(sents))
	for s, sent in enumerate(sents):
		terms = list(set(re.findall(r'[a-z]+', sent.lower())))
		terms = [term for term in terms if not gf.is_generic(term)]
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
	terms = [term for term in terms if not gf.is_generic(term)]
	return best_idx


def valid_sentences(text):
	sents = gf.get_sentences(text)
	sents = [sent for sent in sents if len(sent) > 50]
	return sents
