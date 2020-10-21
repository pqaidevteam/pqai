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
        """Return best combinations as index pairs
        
        Args:
            n (int, optional): Number of combinations needed
        
        Returns:
            list: List of integer tuples representing indexes of documents
                in the `docs` list
        """
        candidates = self._possible_combinations()
        distances = [self._distance(i, j) for i, j in candidates]
        ranked_candidates = [candidates[i] for i in np.argsort(distances)]
        exclusive = self._exclusive_combinations(ranked_candidates)
        top_n = exclusive[:n]
        return top_n if n > 1 else top_n[0]

    def _possible_combinations(self):
        pairs = []
        for i in range(self._ndocs):
            for j in range(i+1, self._ndocs):
                pair = set([i, j])
                pairs.append(pair)
        return pairs

    def _distance(self, i, j):
        if self._matrix is None:
            self._initialize_disclosure_matrix()
        matches_i = self._matrix[i]
        matches_j = self._matrix[j]
        rows = np.array([matches_i, matches_j])
        f1 = self._improvement_distance
        f2 = self._feature_wise_best_distance
        f3 = self._weakest_feature_distance
        return f3(rows)
    
    def _weakest_feature_distance(self, rows):
        """
        Disclosure of the least supported features governs the overall distance.
        """
        feature_wise_minimum = rows.min(axis=0)
        distance = feature_wise_minimum.max()
        return distance
    
    def _feature_wise_best_distance(self, rows):
        """
        Best feature-wise disclosures govern the overall distance.
        """
        feature_wise_minimum = rows.min(axis=0)
        distance = feature_wise_minimum.mean()
        return distance
    
    def _improvement_distance(self, rows):
        """
        The improvement in the score by combining the results governs overall distance
        """
        individual_distances = [row.mean() for row in rows]
        individual_best = np.min(individual_distances)
        combined_best = self._feature_wise_best_distance(rows)
        distance =  combined_best - individual_best # more negative, better
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
    
    def _exclusive_combinations(self, combinations):
        seen = set([])
        exclusive = []
        for combination in combinations:
            if all([e not in seen for e in combination]):
                exclusive.append(combination)
                seen = seen.union(combination)
        return exclusive