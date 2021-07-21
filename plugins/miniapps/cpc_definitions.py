import os
import json
import sys
from pathlib import Path
BASE_DIR = str(Path(__file__).parent.parent.parent.resolve())
sys.path.append(BASE_DIR)

CPC_DATA_FILE = f'{BASE_DIR}/models/cpc_data.json'


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

        
class CPCDefinitionRetriever(metaclass=Singleton):
    """ Retrieves heirarchial definition for all the parts of a CPC. 
    """
    def __init__(self):
        self._lut = None
        self.cpc_data = None     

    def define(self, cpc, segmented=True):
        if not self._lut:
            self._load()
        if not self._lut.get(cpc):
            return None
        
        if not segmented:
            return self._full_def(cpc)

        definition = []
        definition.append([cpc, self._partial_def(cpc)])
        for parent in self._get_parents(cpc):
            definition.append([parent, self._partial_def(parent)])
        definition.reverse()
        return definition

    def _partial_def(self, symbol):
        definition = self._lut.get(symbol)['title_part']
        if isinstance(definition, str):
            return definition
        else:
            return '; '.join(definition) 

    def _full_def(self, symbol):
        return self._lut.get(symbol)['title_full']

    def _get_parents(self, symbol):
        return self._lut.get(symbol)['parents']

    def _load(self):
        self.cpc_data = []
        with open(CPC_DATA_FILE, 'r') as file:
            for line in file:
                self.cpc_data.append(json.loads(line))
        self._lut = self._create_lookup_dict()

    def _create_lookup_dict(self):
        cpc_data_dict = {}
        for d in self.cpc_data:
            cpc_data_dict[d['symbol']] = { key:val for key, val in d.items()
                                                if key != 'symbol'}
        return cpc_data_dict