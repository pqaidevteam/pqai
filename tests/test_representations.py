import unittest

import sys
from pathlib import Path
test_dir = str(Path(__file__).parent.resolve())
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR.resolve()))

from core.encoders import EmbeddingMatrix, BagOfVectorsEncoder
from core.representations import BagOfVectors
from core.representations import BagOfEntities

class TestBagOfVectorsClass(unittest.TestCase):

	def setUp(self):
		emb_matrix_file = f'{test_dir}/test_embs.tsv'
		emb_matrix = EmbeddingMatrix.from_tsv(emb_matrix_file)
		self.encoder = BagOfVectorsEncoder(emb_matrix)

	def test_word_mover_distance_same_sets(self):
		entities = set([ 'base', 'station' ])
		bov1 = self.encoder.encode(entities)
		bov2 = self.encoder.encode(entities)
		dist = BagOfVectors.wmd(bov1, bov2)
		self.assertEqual(0.0, dist)

	def test_word_mover_distance_two_vectors(self):
		bov1 = self.encoder.encode(set([ 'station' ]))
		bov2 = self.encoder.encode(set([ 'stations' ]))
		dist = BagOfVectors.wmd(bov1, bov2)
		self.assertGreater(0.001, dist)

class TestBagOfEntitiesClass(unittest.TestCase):

	def setUp(self):
		self.ents = set(['coffee_cup', 'coffee', 'cup',
			'base_station', 'base_station_antenna'])

	def test_filter_out_overlapping(self):
		expected = set(['coffee_cup', 'base_station_antenna'])
		boe = BagOfEntities(self.ents).non_overlapping()
		self.assertEqual(expected, boe)

if __name__ == '__main__':
    unittest.main()