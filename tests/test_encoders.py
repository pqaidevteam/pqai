import unittest

import sys
from pathlib import Path
test_dir = str(Path(__file__).parent.resolve())
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR.resolve()))

from core.encoders import Encoder
from core.encoders import BagOfEntitiesEncoder
from core.encoders import EmbeddingMatrix
from core.encoders import BagOfVectorsEncoder

class TestEncoderClass(unittest.TestCase):

	def setUp(self):
		self.dummy_encoder_fn = lambda string: list(string)

	def test_encoder_operation(self):
		encoder = Encoder(self.dummy_encoder_fn)
		data = 'hello'
		expected = ['h', 'e', 'l', 'l', 'o']
		actual = encoder.encode(data)
		self.assertEqual(expected, actual)

	def test_can_set_encoding_fn_afterwards(self):
		encoder = Encoder()
		encoder.set_encoding_fn(list)
		data = 'hello'
		expected = ['h', 'e', 'l', 'l', 'o']
		actual = encoder.encode(data)
		self.assertEqual(expected, actual)

	def test_encoder_operation_without_encoder_fn(self):
		def encode():
			encoder = Encoder()
			return encoder.encode('hello')
		self.assertRaises(Exception, encode)

	def test_input_validation(self):
		fn = lambda x: isinstance(x, str)
		encoder = Encoder(list)
		encoder.set_input_validation_fn(fn)
		a = encoder.can_encode('hello')
		b = encoder.can_encode([0, 2, 3])
		self.assertEqual((True, False), (a, b))

	def test_can_encode_array_of_items(self):
		encoder = Encoder(list)
		inputs = ['hi', 'hello']
		expected = [list('hi'), list('hello')]
		actual = encoder.encode_many(inputs)
		self.assertEqual(expected, actual)


class TestBagOfEntitiesEncoderClass(unittest.TestCase):

	def setUp(self):
		file = f'{test_dir}/test_entities.vocab'
		self.boe_encoder = BagOfEntitiesEncoder.from_vocab_file(file)

	def test_can_encode_string(self):
		res = self.boe_encoder.can_encode('This is a sample text.')
		self.assertTrue(res)

	def test_can_encode_array(self):
		res = self.boe_encoder.can_encode([1, 2, 3])
		self.assertFalse(res)

	def test_extract_entities_from_one_sentence(self):
		sent = 'base station and mobile station'
		expected = set([ 'base station', 'mobile station'])
		actual = self.boe_encoder.encode(sent)
		self.assertEqual(expected, actual)

	def test_extract_entities_from_two_sentences(self):
		sents = 'Base station and mobile. Station is there.'
		expected = set(['base station'])
		actual = self.boe_encoder.encode(sents)
		self.assertEqual(expected, actual)

	def test_with_string_devoid_of_entities(self):
		trivial_string = 'the of and'
		actual = self.boe_encoder.encode(trivial_string)
		self.assertEqual(set(), actual)

	def test_with_degenerate_string(self):
		null_string = ''
		actual = self.boe_encoder.encode(null_string)
		self.assertEqual(set(), actual)

	def test_captures_hyphenated_entities(self):
		string = "This is an X-ray machine."
		expected = set(['x-ray'])
		actual = self.boe_encoder.encode(string)
		self.assertEqual(expected, actual)


class TestEmbeddingMatrixClass(unittest.TestCase):

	def setUp(self):
		file = f'{test_dir}/test_embs.tsv'
		self.emb = EmbeddingMatrix.from_tsv(file)

	def test_get_embedding_by_word(self):
		item = 'base'
		expected_emb = [1.0, 0.0]
		actual_emb = list(self.emb[item])
		self.assertEqual(expected_emb, actual_emb)

	def test_can_get_dimensions(self):
		n_dim = self.emb.dims
		self.assertEqual(2, n_dim)

	def test_similar_items(self):
		item = 'station'
		similars = self.emb.similar_to_item(item)
		most_similar = similars[1]  # [0] is the item itself
		self.assertEqual('stations', most_similar)

	def test_whether_item_exists_in_matrix(self):
		a = 'station' in self.emb
		b = 'stationary' in self.emb
		self.assertTrue(a)
		self.assertFalse(b)


class TestBagOfVectorsEncoder(unittest.TestCase):

	def setUp(self):
		emb_matrix_file = f'{test_dir}/test_embs.tsv'
		emb_matrix = EmbeddingMatrix.from_tsv(emb_matrix_file)
		self.encoder = BagOfVectorsEncoder(emb_matrix)
		
	def test_can_encode_simple_entity_set(self):
		entities = set([ 'base', 'station' ])
		base_vec = tuple([1.0, 0.0])
		station_vec = tuple([0.1, 2.0])
		expected_bov = set([base_vec, station_vec])
		bov = self.encoder.encode(entities)
		self.assertEqual(expected_bov, bov)


if __name__ == '__main__':
    unittest.main()