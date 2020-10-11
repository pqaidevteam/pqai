import numpy as np
from core.encoders import default_boe_encoder as boe_encoder
from core.encoders import default_bov_encoder as bov_encoder
from scipy.spatial import distance

class Combiner():

	def __init__(self, query, docs):
		self._query = query
		self._docs = docs
		self._features = self._extract_features(self._query)
		self._ndocs = len(self._docs)
		self._nfeats = len(self._features)
		self._matrix = None

	def get_combinations(self, n=1):
		candidates = self._possible_combinations()
		distances = [self._distance(i, j) for i, j in candidates]
		ranked_candidates = [candidates[i] for i in np.argsort(distances)]
		top_n = ranked_candidates[:n]
		combinations = [set([self._docs[i], self._docs[j]]) for i, j in top_n]
		return combinations if n > 1 else combinations[0]

	def _possible_combinations(self):
		pairs = []
		for i in range(self._ndocs):
			for j in range(i+1, self._ndocs):
				pairs.append((i, j))
		return pairs

	def _distance(self, i, j):
		if self._matrix is None:
			self._initialize_disclosure_matrix()
		matches_i = self._matrix[i]
		matches_j = self._matrix[j]
		rows = np.array([matches_i, matches_j])
		feature_wise_distances = rows.min(axis=0)
		distance = feature_wise_distances.max()	# the weakest feature
		return distance

	def _initialize_disclosure_matrix(self):
		self._matrix = np.zeros((self._ndocs, self._nfeats))
		for i, doc in enumerate(self._docs):
			for j, feature in enumerate(self._features):
				self._matrix[i][j] = self._match(feature, doc)
		return self._matrix

	def _extract_features(self, text):
		entities = boe_encoder.encode(text)
		features = bov_encoder.encode(entities)
		return features

	def _match(self, feature, doc):
		doc_features = self._extract_features(doc)
		min_dist = np.min([distance.cosine(df, feature) for df in doc_features])
		return min_dist

	
