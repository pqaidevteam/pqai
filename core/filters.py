import re
from dateutil.parser import parse as parse_date
from concurrent.futures import ThreadPoolExecutor
import core.db as db

class Filter():

	"""Base class for implementing a Filter criterion on search result triplets
	"""
	
	def __init__(self, filter_fn=None):
		self._filter_fn = filter_fn

	def apply(self, items, n=None):
		assert all(isinstance(i, list) and len(i) == 3 for i in items)
		doc_ids = [item[0] for item in items]
		filtrate, batch_size = [], 128
		for i in range(0, len(doc_ids), batch_size):
			batch = doc_ids[i:i+batch_size]
			docs = db.get_documents(batch)

			for item, doc in zip(items[i:i+batch_size], docs):
				if self._filter_fn(doc):
					filtrate.append(item)
					if n is not None and len(filtrate) == n:
						break
		return filtrate

	def passed_by(self, item):
		doc_id = item[0]
		doc = db.get_document(doc_id)
		return self._filter_fn(doc)

class FilterArray(Filter):

	"""A cascade of filters that acts as a single filter
	"""
	
	def __init__(self, filters=None):
		self._filters = [] if not filters else filters
	
	def apply(self, items, n=None):
		if not self._filters:
			return items if n is None else items[:n]
		return super().apply(items, n)

	def _filter_fn(self, doc):
		for fltr in self._filters:
			if not fltr._filter_fn(doc):
				return False
		return True

	def add(self, the_filter):
		self._raise_if_invalid_filter(the_filter)
		self._filters.append(the_filter)

	def _raise_if_invalid_filter(self, fltr):
		if not isinstance(fltr, Filter):
			msg = 'Only instances of Filter can be added to FilterArray.'
			raise Exception(msg)

class DateFilter(Filter):

	"""Base class for implementing date filters, e.g. publication date
	"""

	def __init__(self, after=None, before=None):
		self._after = parse_date(after) if after is not None else None
		self._before = parse_date(before) if before is not None else None

	def _filter_fn(self, doc):
		if not hasattr(self, '_get_date'):
			raise Exception('DateFilter is an abstract class and should not be instantiated directly.')
		try:
			date = self._get_date(doc)
		except:
			return False # date information missing; exclude patent

		if self._after is not None and date < self._after:
			return False
		if self._before is not None and date > self._before:
			return False
		return True


class PublicationDateFilter(DateFilter):
	
	def __init__(self, after=None, before=None):
		super().__init__(after, before)
	
	def _get_date(self, doc):
		is_npl = 'publicationNumber' not in doc # npl docs have an 'id' field in place of 'publicationNumber'
		date = f"{str(doc['year'])}-12-31" if is_npl else doc['publicationDate']
		return parse_date(date)


class FilingDateFilter(DateFilter):
	
	def __init__(self, after=None, before=None):
		super().__init__(after, before)
		self._get_date = lambda doc: parse_date(doc['filingDate'])


class PriorityDateFilter(DateFilter):
	
	def __init__(self, after=None, before=None):
		super().__init__(after, before)
		self._get_date = lambda doc: parse_date(doc['priorityDate'])


class DocTypeFilter(Filter):
	
	def __init__(self, doctype):
		self._doctype = doctype
	
	def _filter_fn(self, doc):
		if self._doctype == 'patent':
			return 'publicationNumber' in doc
		elif self._doctype == 'npl':
			return 'id' in doc
		else:
			raise Exception(f"Invalid document type: {self._doctype}")

class AssigneeFilter(Filter):
	
	def __init__(self, name):
		self._name = name
	
	def _filter_fn(self, doc):
		if 'assignees' not in doc:
			return False

		# if any assignee name starts with the given name, return True
		return any([assignee['name'].lower().startswith(self._name.lower()) for assignee in doc['assignees']])
	

class KeywordFilter(Filter):

	def __init__(self, keyword, exclude=False):
		self._keyword = keyword
		self._regex = self._create_regex(keyword)
		self._exclude = exclude

	def _filter_fn(self, doc):
		text = doc['title'].lower() + "\n" + doc['abstract'].lower()
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

class CountryCodeFilter(Filter):

	def __init__(self, codes):
		self._country_codes = tuple(codes)
	
	def _filter_fn(self, doc):
		if 'publicationNumber' not in doc:
			return False
		return doc['publicationNumber'].startswith(self._country_codes)
