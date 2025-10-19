from pydantic import BaseModel, Field
from typing import Optional
from core.documents import Document, Patent
from .base import APIRequest

class DocumentRequestSchema(BaseModel):
    id: str = Field(min_length=1)

class DocumentRequest(APIRequest):
    _schema = DocumentRequestSchema

    def __init__(self, req_data):
        super().__init__(req_data)
        self._doc_id = req_data['id']

    def _serve(self):
        doc_id = self.id
        return Document(doc_id).json()


class PatentDataRequestSchema(BaseModel):
    pn: str = Field(pattern=r'^US(RE)?\d{4,11}[AB]\d?$')
    fields: Optional[str] = Field(default=None)

class PatentDataRequest(APIRequest):

    _schema = PatentDataRequestSchema

    def __init__(self, req_data):
        super().__init__(req_data)
        self._pn = req_data['pn']
        self._patent = Patent(self._pn)

    def _serve(self):
        patent_data = {
            'pn': self._patent.publication_id,
            'title': self._patent.title,
            'abstract': self._patent.abstract,
            'description': self._patent.description,
            'claims': self._patent.claims,
            'independent_claims': self._patent.independent_claims,
            'publication_date': self._patent.publication_date,
            'filing_date': self._patent.filing_date,
            'priority_date': self._patent.priority_date,
            'inventors': self._patent.inventors,
            'assignees': self._patent.assignees,
            'cpcs': self._patent.cpcs,
            'citations_backward': self._patent.backward_citations,
            'citations_forward': self._patent.forward_citations
        }
        if self.fields:
            fields = [f.strip().lower() for f in self.fields.split(',')]
            patent_data = {k: v for k, v in patent_data.items() if k in fields}
        return patent_data