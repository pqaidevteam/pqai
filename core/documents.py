import re
from dataclasses import dataclass
from functools import cached_property
from dateutil.parser import parse as parse_date

from core import db
from core import utils


@dataclass
class Document:
    _id: str
    _data: dict = None
    _config = {
        "patent": {
            "publication_id": "publicationNumber",
            "publication_date": "publicationDate",
            "filing_date": "filingDate",
            "priority_date": "priorityDate",
            "backwards_citations": "backwardCitations",
            "forwards_citations": "forwardCitations",
            "www_link": lambda data: utils.get_external_link(
                data.get("publicationNumber")
            ),
            "alias": lambda data: utils.get_faln(data.get("inventors")),
            "full_text": lambda data: db.get_full_text(data.get('publicationNumber')),
        },
        "npl": {
            "publication_id": lambda data: data.get("doi", "[External link]"),
            "abstract": "abstract",
            "www_link": lambda data: data.get("url", data.get("doi")),
            "inventors": lambda data: data.get("authors", []),
            "alias": lambda data: utils.get_faln(data.get("authors", [])),
            "full_text": lambda data: data.get("title")
                + "\n"
                + data.get("abstract"),
            "publication_date": lambda data: f"{data.get('year')}-12-31",
        },
    }

    @cached_property
    def id(self):
        return self._id

    @cached_property
    def type(self):
        pattern = r'^[A-Z]{2}'
        return "patent" if re.match(pattern, self._id) else "npl"

    @cached_property
    def data(self):
        if not self._data:
            self._load()
        return self._data

    def _load(self, force=False):
        if self._data is None or force:
            self._data = db.get_document(self._id)

    def __getattr__(self, key):
        if not self._data:
            self._load()

        if key in self._data:
            return self._data[key]

        if key in self._config[self.type]:
            if callable(self._config[self.type][key]):
                return self._config[self.type][key](self._data)
            return self._data.get(self._config[self.type][key])

        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{key}'")

    @cached_property
    def owner (self):
        if self.type == 'patent':
            arr = self.data.get('assignees')
            if (isinstance(arr, list) and len(arr) and arr[0].strip()):
                return arr[0]

            arr = self.data.get('applicants')
            if (isinstance(arr, list) and len(arr) and arr[0].strip()):
                return arr[0]

            return 'Assignee N/A'

        elif self.type == 'npl':
            if not self.data['authors']:
                return 'Author N/A'
            names = self.data.get('authors', [])
            return utils.get_faln(names)
        return None

    def is_published_before(self, date):
        if date is None:
            return True
        return parse_date(self.publication_date) < parse_date(date)

    def is_published_after(self, date):
        if date is None:
            return True
        return parse_date(self.publication_date) > parse_date(date)

    def is_published_between(self, d0, d1):
        return self.is_published_after(d0) and self.is_published_before(d1)

    def json(self):
        data = {
            "id": self._id,
            "type": self.type,
            "publication_id": self.publication_id,
            "title": self.data.get("title"),
            "abstract": self.data.get("abstract", self.data.get("paperAbstract")),
            "publication_date": self.publication_date,
            "www_link": self.www_link,
            "owner": self.owner,
            "image": getattr(self, "image", None),
            "alias": self.alias,
            "inventors": self.inventors,
        }
        if self.type == "patent":
            data.update({
                "filing_date": self.filing_date,
                "priority_date": self.priority_date,
            })
        return data


class Patent(Document):

    def __init__(self, patent_number):
        super().__init__(patent_number)

    def _load(self, force=False):
        if not self._data or force:
            self._data = db.get_patent_data(self._id)

    @cached_property
    def claims(self):
        return self.data.get("claims", [])

    @cached_property
    def filing_date(self):
        return self.data.get("filingDate")

    @cached_property
    def first_claim(self):
        return self.claims[0] if self.claims else None

    @cached_property
    def description(self):
        return self.data.get("description")

    @cached_property
    def cpcs(self):
        patent = db.get_patent_data(self._id, False)
        return patent.get("cpcs", [])

    @cached_property
    def independent_claims(self):
        pattern = r"\bclaim(s|ed)?\b"
        return [clm for clm in self.claims if not re.search(pattern, clm)]

    @cached_property
    def art_unit(self):
        try:
            examiner = self.data["examinersDetails"]["details"][0]
            return examiner["name"]["department"]
        except (KeyError, IndexError):
            return None

    @cached_property
    def forward_citations(self):
        patent = db.get_patent_data(self._id, False)
        return patent.get("forwardCitations", [])

    @cached_property
    def backward_citations(self):
        patent = db.get_patent_data(self._id, False)
        return patent.get("backwardCitations", [])

class Paper(Document):
    pass
