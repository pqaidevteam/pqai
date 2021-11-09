import numpy as np
import re
import json
import os
from functools import lru_cache
from tensorflow.keras.models import load_model
from tensorflow.keras.models import Model
import tensorflow.keras.backend as K
K.set_image_data_format("channels_last")

from config.config import models_dir

class SensibleSpanExtractor():

	vocab_dict_file = os.path.join(models_dir, 'span_extractor_dictionary.json')
	vocab_file = os.path.join(models_dir, 'span_extractor_vocab.json')
	model_file = os.path.join(models_dir, 'span_extractor_model.hdf5')
	embeddings_file = os.path.join(models_dir, 'span_extractor_vectors.txt')

	def __init__(self):
		self._model = None
		self._dims = 16
		self._vocab_size = 844
		self._dict = {}
		self._embs = {}
		self._emb_matrix = np.empty((self._vocab_size, self._dims))
		self._vocab_map = {}
		self._punct_map = {
			'!': '<exclm>',
			'"': '<dinvc>',  
			'#': '<hash>',  
			'$': '<dlr>',
			'%': '<pcnt>', 
			'&': '<and>', 
			"'": '<sinvc>', 
			'(': '<lb>',  
			')': '<rb>',  
			'*': '<astk>',  
			'+': '<plus>',  
			',': '<coma>',  
			'-': '<minus>',  
			'.': '<fstp>',  
			'/': '<fslsh>',  
			':': '<cln>',  
			';': '<scln>',  
			'<': '<lt>',  
			'=': '<eq>',  
			'>': '<gt>',  
			'?': '<qm>',  
			'@': '<arte>',  
			'[': '<lsb>',  
			'\\': '<bslsh>',  
			']': '<rsb>',  
			'^': '<rtp>',  
			'_': '<uscr>',  
			'`': '<btck>',  
			'{': '<lcb>',  
			'|': '<pipe>',  
			'}': '<rcb>',  
			'~': '<tlde>',  
			'“': 'sdinvc',  
			'”': 'edinvc'
		}
		self.chars = 'abcdefghijklmnopqrstuvwxyz'
		self.MIN_LEN = 6
		self.MAX_LEN = 30

		self._load_model()
		self._load_dict()
		self._load_embeddings()
		self._load_embedding_matrix()
		self._load_vocab_map()

	def _load_model(self):
		model = load_model(self.model_file)
		self._model = Model(model.input[:2], model.layers[-3].output)

	def _load_dict(self):
		with open(self.vocab_dict_file, 'r') as file:
			self._dict = json.load(file)

	def _load_embeddings(self):
		with open(self.embeddings_file, 'r') as file:
			lines = file.read().strip().splitlines()
		for line in lines:
			token, *vector = line.strip().split()
			self._embs[token] = np.array(vector, dtype='float32')
		self._include_pad_unk_vectors()

	def _include_pad_unk_vectors(self):
		low = -0.00001
		high = 0.00001
		self._embs['<pad>'] = [np.random.uniform(low, high) 
			for _ in range(self._dims)]
		self._embs['<unk>'] = self._embs['<raw_unk>']
		self._embs.pop('<raw_unk>')

	def _load_embedding_matrix(self):
		for word, i in self._dict.items():
			self._emb_matrix[i] = self._embs[word]

	def _load_vocab_map(self):
		with open(self.vocab_file, 'r') as fd:
			vocab = json.load(fd)
			self._vocab_map = {word:True for word in vocab}

	def extract_from(self, sentence):
		candidates = self._encode_for_nn(sentence)
		i = self._rank(candidates)[0]
		return self._strip_punctuations(' '.join(candidates[0][i]))

	@lru_cache(maxsize=50000)
	def return_ranked(self, sentence):
		candidates = self._encode_for_nn(sentence)
		ns = self._rank(candidates)
		spans = [self._strip_punctuations(' '.join(candidates[0][n])) for n in ns]
		spans = [s for s in spans if self._passes_post_filter(s)]
		return spans

	def _passes_post_filter(self, span):
		if ')' in span and '(' not in span:
			return False
		if '(' in span and ')' not in span:
			return False
		return True

	def _rank(self, candidates):
		tokens, X_chargrams, X_word_vectors = candidates
		pred = self._model.predict([X_word_vectors, X_chargrams]).flatten()
		pred = K.softmax(pred)
		return np.argsort(pred)[::-1]

	def _encode_for_nn(self, sentence):
		cased = self._tokenize(sentence, lower=False)
		uncased = [t.lower() for t in cased]
		limits = [self.MIN_LEN, self.MAX_LEN]
		tokens = SubsequenceExtractor(cased).extract(*limits)
		spans = SubsequenceExtractor(uncased).extract(*limits)
		chargrams = [self._span2chargram(span) for span in spans]
		word_vectors = [self._embed_words(span) for span in spans]
		return tokens, np.array(chargrams), np.array(word_vectors)

	def _tokenize(self, sentence, lower=True):
		sentence = sentence.lower() if lower else sentence
		tokens = re.findall(r'(\w+|\W+)', sentence)
		tokens = [t for t in tokens if t.strip()]
		return tokens

	def _span2chargram(self, span):
		span_len = min(len(span), self.MAX_LEN)
		span_chargram_unpadded = [self._word2chargram(span[i]) for i in range(span_len)]
		span_chargram = self._padding_int_arr(span_chargram_unpadded)
		return span_chargram

	def _word2chargram(self, word):   
		chargrams =[0]*20
		char_list = list(word)
		for i in range(min(len(char_list), 20)):
			if char_list[i] in self.chars:
				chargrams[i] = self.chars.index(char_list[i])+1
		return chargrams

	def _embed_words(self, span):
		span_len = min(len(span), self.MAX_LEN)
		span_int_array = self._to_int_array(span)
		span_word_emb_unpadded = [self._emb_matrix[span_int_array[i]] for i in range(span_len)]
		span_word_emb = self._padding_int_arr(span_word_emb_unpadded)
		return span_word_emb

	def _get_masked_tokens(self, sent_tokens):
		masked_sent_tokens = []
		for token in sent_tokens:
			if self._is_number(token):
				masked_sent_tokens.append('<num>')
			elif self._is_alphanumeric(token, 'fast'):
				masked_sent_tokens.append('<alphanum>')
			elif token in self._punct_map:
				masked_sent_tokens.append(self._punct_map[token])
			elif token not in self._vocab_map:
				masked_sent_tokens.append('<unk>')
			else:
				masked_sent_tokens.append(token)
		return masked_sent_tokens

	def _is_alphanumeric(self, token, mode='slow'):
		if token.isalnum(): 
			if not token.isalpha():
				if mode == 'slow':
					if is_number(token):
						return False
				return True 
		return False

	def _is_number(self, token):
		return bool(re.search(r'^\d+(\.\d+)?$', token))

	def _encode_tokens(self, tokens):
		encoded_tokens = []
		for token in tokens:
			default = self._dict['<unk>']
			encoded_tokens.append(self._dict.get(token, default))
		return encoded_tokens

	def _to_int_array(self, sent_tokens):
		masked_sent_tokens = self._get_masked_tokens(sent_tokens)
		encoded_tokens = self._encode_tokens(masked_sent_tokens)
		return encoded_tokens

	def _get_pad_token(self, int_arr):
		if len(int_arr[0]) == 16:
			pad_token = self._emb_matrix[0]
		else:
			pad_token = self._word2chargram('0')
		return pad_token

	def _padding_int_arr(self, int_arr):
		pad_token = self._get_pad_token(int_arr)
		for j in range(self.MAX_LEN-len(int_arr)):
			int_arr.append(pad_token)
		int_arr = np.array(int_arr)
		return int_arr

	def _strip_punctuations(self, text):
		patterns = [
			r'\s([\!\%\)\,\.\:\;\?\]\}\”])', # no space before these symbols
			r'([\"\#\$\(\@\[\\\{\“])\s', # no space after these
			r'\s([\'\*\+\-\/\<\=\>\^\_\`\|\~])\s'] # no space before/after
		for pattern in patterns:
			text = re.sub(pattern, r'\1', text)
		text = re.sub('  ', ' ', text) # remove double spaces
		return text

class SubsequenceExtractor():

	def __init__(self, sequence):
		self._seq = sequence
		self._seqlen = len(sequence)

	def extract(self, minlen, maxlen=None):
		maxlen = minlen if maxlen is None else maxlen
		subsequences = []
		for L in self._possible_lengths(minlen, maxlen):
			subsequences += self._get_subsequences_of_length(L)
		return subsequences

	def _possible_lengths(self, minlen, maxlen):
		if self._seqlen <= minlen:
			return [self._seqlen]
		elif minlen < self._seqlen <= maxlen:
			return list(range(minlen, self._seqlen+1))
		else: # n_tokens > maxlen
			return list(range(minlen, maxlen+1))

	def _get_subsequences_of_length(self, L):
		if L == 0:
			return []
		start_positions = range(self._seqlen-L+1)
		return [self._seq[p:p+L] for p in start_positions]