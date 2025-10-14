import re
from functools import cached_property
from dateutil.parser import parse as parse_date

from core.db import patent_db, npl_db
from core import utils


class Document:
    def __init__(self, doc_id):
        self._id = doc_id
        self._proxy = None

    @cached_property
    def id(self):
        return self._id

    @cached_property
    def type(self):
        pattern = r'^[A-Z]{2}'
        return "patent" if re.match(pattern, self._id) else "npl"

    @property
    def _data(self):
        """Lazy load the document proxy from the appropriate database"""
        if self._proxy is None:
            if self.type == "patent":
                self._proxy = patent_db.get(self._id)
            else:
                self._proxy = npl_db.get(self._id)
            
            # If database returns None, raise an error
            if self._proxy is None:
                raise ValueError(f"Document {self._id} not found in database")
        return self._proxy
    
    @cached_property
    def data(self):
        """Alias for backward compatibility - returns the proxy"""
        return self._data

    def __getattr__(self, key):
        """
        Fallback for any attribute not explicitly defined.
        Allows accessing raw data fields directly for backward compatibility.
        """
        # Avoid infinite recursion for special attributes
        if key.startswith('_'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{key}'")
        
        # Try to get from the data proxy
        try:
            return self._data.get(key)
        except Exception:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{key}'")
    
    # Common properties for all documents
    
    @cached_property
    def title(self):
        return self._data.get("title")
    
    @cached_property
    def abstract(self):
        return self._data.get("abstract") or self._data.get("paperAbstract")
    
    @cached_property
    def publication_date(self):
        if self.type == "patent":
            return self._data.get("publicationDate")
        else:
            year = self._data.get("year")
            return f"{year}-12-31" if year else None
    
    @cached_property
    def publication_id(self):
        if self.type == "patent":
            return self._data.get("publicationNumber")
        else:
            return self._data.get("doi", "[External link]")
    
    @cached_property
    def inventors(self):
        if self.type == "patent":
            return self._data.get("inventors", [])
        else:
            return self._data.get("authors", [])
    
    @cached_property
    def www_link(self):
        if self.type == "patent":
            return utils.get_external_link(self._data.get("publicationNumber"))
        else:
            return self._data.get("url") or self._data.get("doi")
    
    @cached_property
    def alias(self):
        return utils.get_faln(self.inventors)
    
    @cached_property
    def full_text(self):
        """Get full text - for patents this combines multiple fields"""
        if self.type == "patent":
            abstract = self.abstract or ""
            # Access to claims and description will trigger S3 load if needed
            claims_list = self._data.get("claims", [])
            claims = "\n".join(claims_list) if claims_list else ""
            desc = self._data.get("description", "")
            desc = re.sub(r"\n+(?=[^A-Z])", " ", desc)  # collapse multiple line breaks
            return "\n".join([abstract, claims, desc])
        else:
            title = self._data.get("title", "")
            abstract = self._data.get("abstract", "")
            return f"{title}\n{abstract}"

    @cached_property
    def owner(self):
        if self.type == 'patent':
            arr = self._data.get('assignees')
            if (isinstance(arr, list) and len(arr) and arr[0].strip()):
                return arr[0]

            arr = self._data.get('applicants')
            if (isinstance(arr, list) and len(arr) and arr[0].strip()):
                return arr[0]

            return 'Assignee N/A'

        elif self.type == 'npl':
            if not self._data.get('authors'):
                return 'Author N/A'
            names = self._data.get('authors', [])
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
            "title": self.title,
            "abstract": self.abstract,
            "publication_date": self.publication_date,
            "www_link": self.www_link,
            "owner": self.owner,
            "image": getattr(self, "image", None),
            "alias": self.alias,
            "inventors": self.inventors,
        }
        if self.type == "patent":
            data.update({
                "filing_date": self._data.get("filingDate"),
                "priority_date": self._data.get("priorityDate"),
            })
        return data


class Patent(Document):

    def __init__(self, patent_number):
        super().__init__(patent_number)

    @cached_property
    def claims(self):
        """Claims are stored in S3 - will trigger lazy load on first access"""
        return self._data.get("claims", [])
    
    @cached_property
    def description(self):
        """Description is stored in S3 - will trigger lazy load on first access"""
        return self._data.get("description", "")

    @cached_property
    def filing_date(self):
        return self._data.get("filingDate")
    
    @cached_property
    def priority_date(self):
        return self._data.get("priorityDate")

    @cached_property
    def first_claim(self):
        return self.claims[0] if self.claims else None

    @cached_property
    def cpcs(self):
        """CPCs are stored in S3 - will trigger lazy load on first access"""
        return self._data.get("cpcs", [])

    @cached_property
    def independent_claims(self):
        pattern = r"\bclaim(s|ed)?\b"
        return [clm for clm in self.claims if not re.search(pattern, clm)]

    @cached_property
    def art_unit(self):
        try:
            examiner = self._data.get("examinersDetails", {})
            details = examiner.get("details", [])
            if details:
                return details[0]["name"]["department"]
        except (KeyError, IndexError, TypeError):
            return None
        return None

    @cached_property
    def forward_citations(self):
        """Forward citations are stored in S3 - will trigger lazy load on first access"""
        return self._data.get("forwardCitations", [])

    @cached_property
    def backward_citations(self):
        """Backward citations are stored in S3 - will trigger lazy load on first access"""
        return self._data.get("backwardCitations", [])
    
    @cached_property
    def full_text(self):
        """Override to use patent-specific implementation"""
        abstract = self.abstract or ""
        claims = "\n".join(self.claims) if self.claims else ""
        desc = self.description
        desc = re.sub(r"\n+(?=[^A-Z])", " ", desc) if desc else ""
        return "\n".join([abstract, claims, desc])

class Paper(Document):
    pass
