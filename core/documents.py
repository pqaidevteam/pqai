from dateutil.parser import parse as parse_date
from core import db
from core import utils
import re

class Document:

	def __init__(self, doc_id):
		self._id = doc_id
		self._data = None	# lazy-load data from DB

	def __getitem__(self, key):
		if self._data is None:
			self._load()
		return self._data.get(key)

	def _load (self, force=False):
		if self._data is None or force == True:
			self._data = db.get_document(self.id)

	def is_patent (self):
		return bool(re.match(r'US\d+', self._id))

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

	def is_published_between (self, earlier_date, later_date):
		return self.is_published_after(earlier_date) \
				and self.is_published_before(later_date)

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
			if not self.data.get('assignees'):
				return 'Assignee N/A'
			elif not self.data.get('assignees')[0].strip():
				return 'Assignee N/A'
			else:
				return self.data['assignees'][0]
		elif self.type == 'npl':
			if not self.data['authors']:
				return 'Author N/A'
			else:
				names = [e['name'] for e in self.data['authors']]
				return utils.get_faln(names)
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

	@property
	def inventors(self):
		if self.type == 'patent':
			return self.data['inventors']
		else:
			return [e['name'] for e in self.data['authors']]

	@property
	def alias(self):
		return utils.get_faln(self.inventors)

	def json(self):
		return dict(
			id = self.id,
			type = self.type,
			publication_id = self.publication_id,
			title = self.title,
			abstract = self.abstract,
			publication_date = self.publication_date,
			www_link = self.www_link,
			owner = self.owner,
			image = self.image if hasattr(self, 'image') else None,
			alias = self.alias,
			inventors = self.inventors
		)

class Patent (Document):
	
	def __init__(self, patent_number):
		super().__init__(patent_number)

	def _load (self, force=False):
		if self._data is None or force == True:
			self._data = db.get_patent_data(self.id)

	@property
	def claims(self):
		return self.data['claims']

	@property
	def filing_date(self):
		return self.data.get('filingDate')

	@property
	def first_claim(self):
		return self.claims[0]

	@property
	def description(self):
		return self.data['description']

	@property
	def cpcs(self):
		biblio = db.get_patent_data(self.id, True)
		return biblio['cpcs']

	@property
	def independent_claims(self):
		pattern = r'\bclaim(s|ed)?\b'
		return [clm for clm in self.claims if not re.search(pattern, clm)]

	@property
	def art_unit(self):
		try:
			examiner = self.data['examinersDetails']['details'][0]
			return examiner['name']['department']
		except:
			return None

	@property
	def forward_citations(self):
		biblio = db.get_patent_data(self.id, True)
		return biblio['forwardCitations']

	@property
	def backward_citations(self):
		biblio = db.get_patent_data(self.id, True)
		return biblio['backwardCitations']

class Paper (Document):
	pass