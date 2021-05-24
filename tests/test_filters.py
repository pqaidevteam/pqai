import unittest
import json

import sys
from pathlib import Path
test_dir = str(Path(__file__).parent.resolve())
BASE_DIR = Path(__file__).parent.parent
sys.path.append(str(BASE_DIR.resolve()))

from core.filters import Filter, FilterArray
from core.filters import PublicationDateFilter, FilingDateFilter
from core.filters import KeywordFilter
from core.documents import Document

class TestFilter(unittest.TestCase):

	def setUp(self):
		def filter_fn(word):
			return word.endswith('ing')
		self.demo_filter = Filter(filter_fn)

	def test_typing_ends_with_ing(self):
		self.assert_does_end_in_ing('typing')
		self.assert_does_end_in_ing('skiing')
		self.assert_does_end_in_ing('ing')

	def test_mouse_ends_with_ing(self):
		self.assert_doesnt_end_in_ing('')
		self.assert_doesnt_end_in_ing('ng')
		self.assert_doesnt_end_in_ing('mouse')
		self.assert_doesnt_end_in_ing('king ')

	def assert_does_end_in_ing(self, word):
		self.assertTrue(self.demo_filter.passed_by(word))

	def assert_doesnt_end_in_ing(self, word):
		self.assertFalse(self.demo_filter.passed_by(word))

	def test_filter_words_ending_in_ing(self):
		words = ['waking', 'wake', 'typing', 'queen', 'king']
		expected = ['waking', 'typing', 'king']
		actual = self.demo_filter.apply(words)
		self.assertEqual(expected, actual)


class TestFilterArray(unittest.TestCase):

	def setUp(self):
		filter_fn_1 = lambda word: word.startswith('pre')
		filter_fn_2 = lambda word: word.endswith('ed')
		self.filter_1 = Filter(filter_fn_1)
		self.filter_2 = Filter(filter_fn_2)
		self.set = ['predetermined', 'prevent',
					'defined', 'precalculated']
		self.subset = ['predetermined', 'precalculated']

	def test_create_filter_in_one_go(self):
		filter_arr = FilterArray([self.filter_1, self.filter_2])
		self.assertFiltrate(filter_arr, self.set, self.subset)

	def test_create_filter_incrementally(self):
		filter_arr = FilterArray()
		filter_arr.add(self.filter_1)
		filter_arr.add(self.filter_2)
		self.assertFiltrate(filter_arr, self.set, self.subset)

	def assertFiltrate(self, filter_arr, items, filtrate):
		expected = filtrate
		actual = filter_arr.apply(items)
		self.assertEqual(expected, actual)


class TestPublicationDateFilter(unittest.TestCase):
	
	def setUp(self):
		self.doc = Document('US7654321B2')

	def test_after_date_filter_operation(self):
		self.assertFalse(self.doc_published_after('2010-02-03'))
		self.assertTrue(self.doc_published_after('2010-02-02'))
		self.assertTrue(self.doc_published_after('2010-02-01'))

	def test_before_date_filter_operation(self):
		self.assertTrue(self.doc_published_before('2010-02-03'))
		self.assertTrue(self.doc_published_before('2010-02-02'))
		self.assertFalse(self.doc_published_before('2010-02-01'))

	def test_between_date_filter_operation(self):
		self.assertTrue(self.doc_published_between('2010-02-01', '2010-02-03'))
		self.assertFalse(self.doc_published_between('2010-01-01', '2010-02-01'))
		self.assertTrue(self.doc_published_between('2010-01-01', '2010-02-02'))
		self.assertTrue(self.doc_published_between('2010-02-02', '2010-02-02'))
		self.assertFalse(self.doc_published_between('2010-02-03', '2010-02-05'))

	def doc_published_after(self, date):
		date_criterion = PublicationDateFilter(date, None)
		return date_criterion.passed_by(self.doc)

	def doc_published_before(self, date):
		date_criterion = PublicationDateFilter(None, date)
		return date_criterion.passed_by(self.doc)

	def doc_published_between(self, d1, d2):
		date_criterion = PublicationDateFilter(d1, d2)
		return date_criterion.passed_by(self.doc)


class TestFilingDateFilter(unittest.TestCase):
	pass


class TestPriorityDateFilter(unittest.TestCase):
	pass


class TestKeywordFilter(unittest.TestCase):
	
	def setUp(self):
		self.doc = Document('US7654321B2')

	def test_simplest_keyword_match(self):
		criterion = KeywordFilter('downhole')
		self.assertTrue(criterion.passed_by(self.doc))
		criterion = KeywordFilter('downholes')
		self.assertFalse(criterion.passed_by(self.doc))

	def test_casing_doesnt_matter(self):
		criterion = KeywordFilter('DoWnHoLE')
		self.assertTrue(criterion.passed_by(self.doc))

	def test_asterisk_usage(self):
		criterion = KeywordFilter('downho*')
		self.assertTrue(criterion.passed_by(self.doc))
		criterion = KeywordFilter('dow*ole')
		self.assertTrue(criterion.passed_by(self.doc))
		criterion = KeywordFilter('downhole*')
		self.assertTrue(criterion.passed_by(self.doc))

	def test_underscore_usage(self):
		criterion = KeywordFilter('down_hole')
		self.assertTrue(criterion.passed_by(self.doc))
		criterion = KeywordFilter('logging_while_drilling')
		self.assertTrue(criterion.passed_by(self.doc))

	def test_single_letter_wildcard_usage(self):
		criterion = KeywordFilter('downhol?')
		self.assertTrue(criterion.passed_by(self.doc))
		criterion = KeywordFilter('downhole?')
		self.assertTrue(criterion.passed_by(self.doc))


if __name__ == '__main__':
    unittest.main()
	