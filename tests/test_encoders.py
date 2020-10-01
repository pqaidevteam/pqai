import unittest

import sys
from pathlib import Path
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR.resolve()))

from core.encoders import Encoder

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
		encoder.encoder_fn = list
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
		validation_fn = lambda x: isinstance(x, str)
		encoder = Encoder(list)
		encoder.input_validation_fn = validation_fn
		a = encoder.is_valid_input('hello')
		b = encoder.is_valid_input([0, 2, 3])
		self.assertEqual((True, False), (a, b))

	def test_can_encode_multiple_inputs_in_one_go(self):
		encoder = Encoder(list)
		inputs = ['hi', 'hello']
		expected = [list('hi'), list('hello')]
		actual = encoder.encode_many(inputs)
		self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()