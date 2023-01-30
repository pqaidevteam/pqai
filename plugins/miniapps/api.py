from collections import Counter
import sys
import re
from pathlib import Path

BASE_DIR = str(Path(__file__).parent.parent.parent.resolve())
THIS_DIR = str(Path(__file__).parent.resolve())
sys.path.append(BASE_DIR)
sys.path.append(THIS_DIR)

from core.api import APIRequest, SearchRequest102, SimilarConceptsRequest
from core.api import BadRequestError, ResourceNotFoundError
from core.documents import Patent
from core.encoders import default_boe_encoder
from cpc_definitions import CPCDefinitionRetriever

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
        all_cpcs = []
        for patent in patents:
            all_cpcs += patent.cpcs

        sections = [cpc[0] for cpc in all_cpcs]
        classes = [cpc[:3] for cpc in all_cpcs]
        subclasses = [cpc[:4] for cpc in all_cpcs]
        groups = [cpc.split("/")[0] + "/00" for cpc in all_cpcs]
        subgroups = all_cpcs.copy()

        section_dist = Counter(sections).most_common()
        class_dist = Counter(classes).most_common()
        subclass_dist = Counter(subclasses).most_common()
        group_dist = Counter(groups).most_common()
        subgroup_dist = Counter(subgroups).most_common()

        confidence = {}
        for section, count in section_dist:
            total = len(sections)
            confidence[section] = count/total

        for clas, count in class_dist:
            section = clas[0]
            total = len([c for c in classes if c.startswith(section)])
            alpha = confidence[section]
            confidence[clas] = alpha*count/total

        for subclass, count in subclass_dist:
            clas = subclass[:3]
            total = len([c for c in subclasses if c.startswith(clas)])
            alpha = confidence[clas]
            confidence[subclass] = alpha*count/total

        for group, count in group_dist:
            subclass = group[:4]
            total = len([g for g in groups if g.startswith(subclass)])
            alpha = confidence[subclass]
            confidence[group] = alpha*count/total

        for subgroup, count in subgroup_dist:
            group = subgroup[:4]
            total = len([sg for sg in subgroups if sg.startswith(group)])
            alpha = confidence[group]
            confidence[subgroup] = alpha*count/total

        output = []
        for cpc, value in confidence.items():
            val = round(value, 2)
            if val < 0.01:
                continue
            try:
                definition = DefineCPC({"cpc": cpc}).serve()
                output.append({"cpc": cpc, "definition": definition, "confidence": val})
            except:
                continue

        output = sorted(output, key=lambda x: x["confidence"], reverse=True)
        return output[:50]

    def _similar_patents(self):
        search_req = {'q': self._text }
        search_req['after'] = '2010-01-01' # base inference on recent data
        search_req['type'] = 'patent'
        search_req['n'] = 100
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
        search_req['n'] = 25
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


class DefineCPC(APIRequest):

    def __init__(self, req_data):
        super().__init__(req_data)
        self._cpc_code = req_data['cpc'].strip()
        self._short = bool(int(req_data.get('short', 0)))

    def _validation_fn(self):
        if not isinstance(self._data.get('cpc'), str):
            raise BadRequestError('Invalid request')
        cpc_pattern = r'[ABCDEFGHY]\d\d[A-Z]\d+\/\d+'
        if not re.match(cpc_pattern, self._data.get('cpc').strip()):
            raise BadRequestError('Invalid CPC code')

    def _serving_fn(self):
        segmented = not self._short
        definition = CPCDefinitionRetriever().define(self._cpc_code, segmented)
        if definition is None:
            err_msg = f'Could not find definition for {self._cpc_code}'
            raise ResourceNotFoundError(err_msg)
        return definition