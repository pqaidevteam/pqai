from dateutil.parser import parse as parse_date
from core import db
from core import utils


class Document:

	def __init__(self, doc_id):
		self._id = doc_id
		self._data = None	# lazy-load data from DB

	def _load (self, force=False):
		if self._data is None or force == True:
			self._data = db.get_document(self.id)

	def is_patent (self):
		return False if len(self._id) == 40 else True

	def is_npl (self):
		return not self.is_patent()

	def is_published_before (self, date):
		if date is None:
			return True
		return parse_date(self.publication_date) < parse_date(date)

	def is_published_after (self, date):
		if date is None:
			return True
		return parse_date(self.publication_date) > parse_date(date)

	def is_published_between (self, before, after):
		return self.is_published_before(before) \
				and self.is_published_after(after)

	@property
	def type (self):
		return 'patent' if self.is_patent() else 'npl'

	@property
	def id (self):
		return self._id

	@property
	def data (self):
		if not self._data:
			self._load()
		return self._data

	@property
	def title (self):
		if self.type == 'patent':
			return self.data['title']
		elif self.type == 'npl':
			return self.data['title']
		else:
			return None

	@property
	def abstract (self):
		if self.type == 'patent':
			return self.data['abstract']
		elif self.type == 'npl':
			return self.data['paperAbstract']
		else:
			return None

	@property
	def publication_date (self):
		if self.type == 'patent':
			return self.data['publicationDate']
		elif self.type == 'npl':
			# If only the publication year is known (and exact date is
			# unknown) consider it published on the last day of the year
			return str(self.data['year']) + '-12-31'
		else:
			return None

	@property
	def www_link (self):
		if self.type == 'patent':
			return utils.get_external_link(self.data['publicationNumber'])
		elif self.type == 'npl':
			if self.data['doiUrl']:
				return self.data['doiUrl']
			else:
				return self.data['s2Url']
		else:
			return None


	@property
	def owner (self):
		if self.type == 'patent':
			return self.data['assignees'][0]
		elif self.type == 'npl':
			return utils.get_faln([e['name'] for e in self.data['authors']])
		else:
			return None

	@property
	def publication_id (self):
		if self.type == 'patent':
			return self.data['publicationNumber']
		elif self.type == 'npl':
			if self.data['doi']:
				return self.data['doi']
			else:
				return '[External link]'
		else:
			return None

	@property
	def full_text(self):
		if self.type == 'patent':
			text = db.get_full_text(self.publication_id)
		else:
			text = self.title + '\n' + self.abstract
		return text

	def to_json(self):
		return dict(
			id = self.id,
			type = self.type,
			publication_id = self.publication_id,
			title = self.title,
			abstract = self.abstract,
			publication_date = self.publication_date,
			www_link = self.www_link,
			owner = self.owner
		)

	

class Patent (Document):
	pass


class Paper (Document):
	pass