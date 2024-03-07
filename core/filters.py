from dateutil.parser import parse as parse_date
import re

class Filter():

	"""Base class for implementing a Filter criterion on items
	"""
	
	def __init__(self, filter_fn=None):
		self._filter_fn = filter_fn

	def apply(self, items):
		filtrate = [r for r in items if self.passed_by(r)]
		return filtrate

	def passed_by(self, item):
		self._raise_if_invalid_filter_fn()
		return self._filter_fn(item)

	def _raise_if_invalid_filter_fn(self):
		if not callable(self._filter_fn):
			raise Exception("Invalid filter function.")


class FilterArray(Filter):

	"""A cascade of filters that acts as a single filter
	"""
	
	def __init__(self, filters=None):
		self._filters = [] if not filters else filters

	def _filter_fn(self, item):
		if len(self._filters) == 0:
			return True
		return all([f.passed_by(item) for f in self._filters])

	def add(self, the_filter):
		self._raise_if_invalid_filter(the_filter)
		self._filters.append(the_filter)

	def _raise_if_invalid_filter(self, fltr):
		if not isinstance(fltr, Filter):
			raise Exception('Only instances of Filter can be added \
								to FilterArray.')

class DateFilter(Filter):

	"""Base class for implementing date filters, e.g. publication date
	"""
	
	def __init__(self, after=None, before=None):
		self._after = parse_date(after) if after is not None else None
		self._before = parse_date(before) if before is not None else None
		self._get_item_date = None

	def _filter_fn(self, item):
		date = self._get_item_date(item)
		if self._after is not None and date < self._after:
			return False
		if self._before is not None and date > self._before:
			return False
		return True


class PublicationDateFilter(DateFilter):
	
	def __init__(self, after=None, before=None):
		super().__init__(after, before)
		self._get_item_date = lambda doc: parse_date(doc.publication_date)


class FilingDateFilter(DateFilter):
	
	def __init__(self, after=None, before=None):
		super().__init__(after, before)
		self._get_item_date = lambda doc: parse_date(doc.filing_date)


class PriorityDateFilter(DateFilter):
	
	def __init__(self, after=None, before=None):
		super().__init__(after, before)
		self._get_item_date = lambda doc: parse_date(doc.priority_date)


class DocTypeFilter(Filter):
	
	def __init__(self, doctype):
		self._doctype = doctype
		self._filter_fn = lambda doc: doc.type == self._doctype

class AssigneeFilter(Filter):
	
	def __init__(self, name):
		self._name = name
		self._filter_fn = lambda doc: doc.owner == self._name

class KeywordFilter(Filter):

	def __init__(self, keyword, exclude=False):
		self._keyword = keyword
		self._regex = self._create_regex(keyword)
		self._exclude = exclude

	def _filter_fn(self, doc):
		text = doc.abstract.lower()
		res = bool(re.search(self._regex, text))
		res = res if not self._exclude else not res
		return res

	def _create_regex(self, keyword):
		regex = keyword.lower()
		regex = re.sub(r'\*+', r'\\w*', regex)
		regex = re.sub(r'\?+', r'\\w?', regex)
		regex = re.sub('_+', r'[\\_\\-\\s]?', regex)
		regex = rf'\b{regex}\b'
		return regex
