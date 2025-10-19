import markdown
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from typing import Optional

from core.encoders import default_boe_encoder, default_embedding_matrix
from core.snippet import SnippetExtractor
from core.vectorizers import SentBERTVectorizer
from core.documents import Patent

from config.config import docs_dir

from .base import APIRequest, ResourceNotFoundError

class PassageRequestSchema(BaseModel):
    q: str = Field(min_length=1)
    pn: str = Field(min_length=1)

class PassageRequest(APIRequest):
    _schema = PassageRequestSchema

    def _format(self, response):
        return {
            'query': self.q,
            'id': self.pn,
            **response
        }

class SnippetRequest(PassageRequest):

    def _serve(self):
        text = Patent(self.pn).full_text
        snippet = SnippetExtractor.extract_snippet(self.q, text)
        return {"snippet": snippet}

class MappingRequest(PassageRequest):

    def _serve(self):
        text = Patent(self.pn).full_text
        mapping = SnippetExtractor.map(self.q, text)
        return {"mapping": mapping}

class ConceptsRequest(APIRequest):

    def __init__(self, req_data):
        super().__init__(req_data)
        self._text = req_data['text']

    def _serve(self):
        return list(default_boe_encoder.encode(self._text))

class PatentDataRequestSchema(BaseModel):
    pn: str = Field(pattern=r'^US(RE)?\d{4,11}[AB]\d?$')

class PatentDataRequest(APIRequest):
    _schema = PatentDataRequestSchema

    def __init__(self, req_data):
        super().__init__(req_data)
        self.patent = Patent(self.pn)

class AbstractConceptsRequest(PatentDataRequest):
    def _serve(self):
        req = ConceptsRequest({'text': self.patent.abstract})
        concepts = req.serve()
        return {'concepts': concepts}

class DescriptionConceptsRequest(PatentDataRequest):
    def _serve(self):
        req = ConceptsRequest({'text': self.patent.description})
        concepts = req.serve()
        return {'concepts': concepts}

class PatentAbstractVectorRequest(PatentDataRequest):
    def _serve(self):
        abstract = self.patent.abstract
        vector = SentBERTVectorizer().embed(abstract)
        return {'vector': vector.tolist()}

class ConceptRelatedRequestSchema(BaseModel):
    concept: str = Field(min_length=1)
    n: Optional[int] = Field(default=10, ge=1, le=100)

class ConceptRelatedRequest(APIRequest):
    _schema = ConceptRelatedRequestSchema

    def __init__(self, req_data):
        super().__init__(req_data)
        self.concept = self.concept.lower()

    def _format(self, response):
        if isinstance(response, dict):
            response['concept'] = self.concept
        return response

class SimilarConceptsRequest(ConceptRelatedRequest):
    def _serve(self):
        if self.concept not in default_embedding_matrix:
            raise ResourceNotFoundError(f'No vector for "{self.concept}"')

        n = 2 * self.n  # because some will be filtered out
        neighbours = default_embedding_matrix.similar_to_item(self.concept, n)
        neighbours = [e for e in neighbours if self.concept not in e][:self.n]
        return {'similar': neighbours}

class ConceptVectorRequest(ConceptRelatedRequest):
    def _serve(self):
        if self.concept not in default_embedding_matrix:
            raise ResourceNotFoundError(f'No vector for "{self.concept}"')

        vector = default_embedding_matrix[self.concept]
        return {'vector': list(vector)}

class DocumentationRequest(APIRequest):
    _template_file = f'{docs_dir}template.html'
    _docs_file = f'{docs_dir}README-API.md'

    def _serve(self):
        template = self._get_template()
        contents = self._get_docs_html()
        template.find('body').append(contents)
        return str(template)

    def _get_template(self):
        with open(self._template_file, 'r') as f:
            html = f.read()
        return BeautifulSoup(html, 'html.parser')

    def _get_docs_html(self):
        with open(self._docs_file, 'r') as f:
            md = f.read()
        exts = ['tables', 'toc', 'smarty', 'codehilite']
        html = markdown.markdown(md, extensions=exts)
        return BeautifulSoup(html, 'html.parser')