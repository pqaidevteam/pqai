import re
from dateutil.parser import parse as parse_date
import core.db as db

class Filter():

	"""Base class for implementing a Filter criterion on search result triplets
	"""
	
	def __init__(self, filter_fn=None):
		self._filter_fn = filter_fn

	def apply(self, items, n=None):
		filtrate = []
		for item in items:
			if self._filter_fn(item):
				filtrate.append(item)
				if n is not None and len(filtrate) == n:
					break
		return filtrate

	def passed_by(self, item):
		return self._filter_fn(item)

class DocumentFilter(Filter):
	
	def apply(self, items, n=None):
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
		filtrate = items.copy()
		for fltr in self._filters:
			filtrate = fltr.apply(filtrate)
		return filtrate[:n]

	def add(self, the_filter):
		assert isinstance(the_filter, Filter), 'Only instances of Filter can be added to FilterArray.'
		self._filters.append(the_filter)

class DateFilter(DocumentFilter):

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
		except Exception:
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
	
	def _get_date(self, doc):
		return parse_date(doc['filingDate'])


class PriorityDateFilter(DateFilter):
	
	def _get_date(self, doc):
		return parse_date(doc['priorityDate'])


class DocTypeFilter(DocumentFilter):
	
	def __init__(self, doctype):
		self._doctype = doctype
	
	def _filter_fn(self, doc):
		if self._doctype == 'patent':
			return 'publicationNumber' in doc
		elif self._doctype == 'npl':
			return 'id' in doc
		else:
			raise Exception(f"Invalid document type: {self._doctype}")

class AssigneeFilter(DocumentFilter):
	
	def __init__(self, name):
		self._name = name
	
	def _filter_fn(self, doc):
		if 'assignees' not in doc:
			return False

		# if any assignee name starts with the given name, return True
		return any([assignee['name'].lower().startswith(self._name.lower()) for assignee in doc['assignees']])
	

class KeywordFilter(DocumentFilter):

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

class CountryCodeFilter(DocumentFilter):

	def __init__(self, codes):
		self._country_codes = tuple(codes)
	
	def _filter_fn(self, doc):
		if 'publicationNumber' not in doc:
			return False
		return doc['publicationNumber'].startswith(self._country_codes)

class FilterExtractor():

    @classmethod
    def extract(cls, req_data):
        filters = FilterArray()
        date_filter = cls._get_date_filter(req_data)
        keyword_filters = cls._get_keyword_filters(req_data)
        country_code_filter = cls._get_country_code_filter(req_data)
        if date_filter:
            filters.add(date_filter)
        if keyword_filters:
            for fltr in keyword_filters:
                filters.add(fltr)
        if country_code_filter:
            filters.add(country_code_filter)
        return filters
	
    @classmethod
    def _get_date_filter(cls, req_data):
        after = req_data.get('after', None)
        before = req_data.get('before', None)
        dtype = req_data.get('dtype', 'publication')
        if after or before:
            after = None if not bool(after) else after
            before = None if not bool(before) else before
            if dtype == 'filing':
                return FilingDateFilter(after, before)
            elif dtype == 'publication':
                return PublicationDateFilter(after, before)
            elif dtype == 'priority':
                return PriorityDateFilter(after, before)
            else:
                raise ValueError('Invalid date filter type.')

    @classmethod
    def _get_keyword_filters(cls, req_data):
        query = req_data.get('q', '')
        keywords = re.findall(r'\`(\-?[\w\*\?]+)\`', query)
        if not keywords:
            return None
        filters = []
        for keyword in keywords:
            if keyword.startswith('-'):
                filters.append(KeywordFilter(keyword[1:], exclude=True))
            else:
                filters.append(KeywordFilter(keyword))
        return filters

    @classmethod
    def _get_country_code_filter(self, req_data):
        cc = req_data.get('cc', None)
        if cc is None:
            return

        codes = re.findall(r'\b[A-Z]{2}\b', cc.upper())
        if codes:
            return CountryCodeFilter(codes)
