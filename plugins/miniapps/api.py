from collections import Counter
import sys
from pathlib import Path

BASE_DIR = str(Path(__file__).parent.parent.parent.resolve())
print(BASE_DIR)
sys.path.append(BASE_DIR)

from core.api import APIRequest, BadRequestError
from core.api import SearchRequest102, SimilarConceptsRequest
from core.documents import Patent
from core.encoders import default_boe_encoder

class TextBasedRequest(APIRequest):

    def __init__(self, req_data):
        super().__init__(req_data)
        self._text = req_data['text']

    def _validation_fn(self):
        if not isinstance(self._data.get('text'), str):
            raise BadRequestError('Invalid request')
        if not self._data.get('text').strip():
            raise BadRequestError('Invalid request')

class SuggestCPCs(TextBasedRequest):
    
    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        patents = self._similar_patents()
        cpcs = []
        for patent in patents:
            cpcs += patent.cpcs
        distribution = Counter(cpcs).most_common(10)
        return [cpc for cpc, freq in distribution]

    def _similar_patents(self):
        search_req = {'q': self._text }
        search_req['after'] = '2015-12-31' # base inference on recent data
        search_req['type'] = 'patent'
        search_req['n'] = 50
        results = SearchRequest102(search_req).serve()['results']
        patents = [Patent(res['id']) for res in results]
        return patents


class PredictGAUs(TextBasedRequest):
    
    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        patents = self._similar_patents()
        pns = [p for p in patents if p.id.endswith(('B1', 'B2', 'A'))]
        gaus = [p.art_unit for p in patents if p.art_unit is not None]
        distribution = Counter(gaus).most_common(3)
        return [gau for gau, freq in distribution]

    def _similar_patents(self):
        search_req = {'q': self._text }
        search_req['after'] = '2015-12-31' # base inference on recent data
        search_req['type'] = 'patent'
        search_req['n'] = 50
        results = SearchRequest102(search_req).serve()['results']
        patents = [Patent(res['id']) for res in results]
        return patents


class SuggestSynonyms(TextBasedRequest):
    
    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        req = SimilarConceptsRequest({'concept': self._text})
        return req.serve()['similar']


class ExtractConcepts(TextBasedRequest):
    
    def __init__(self, req_data):
        super().__init__(req_data)

    def _serving_fn(self):
        return list(default_boe_encoder.encode(self._text))