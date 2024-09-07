import sys
from pathlib import Path
BASE_DIR = str(Path(__file__).parent.resolve())
sys.path.append(BASE_DIR)

from __main__ import app, add_routes
import api as API

route_config = [
    {"method": "GET", "path": "/suggest/cpcs", "handler": API.SuggestCPCs},
    {"method": "GET", "path": "/predict/gaus", "handler": API.PredictGAUs},
    {"method": "GET", "path": "/suggest/synonyms", "handler": API.SuggestSynonyms},
    {"method": "GET", "path": "/extract/concepts", "handler": API.ExtractConcepts},
    {"method": "GET", "path": "/definitions/cpcs", "handler": API.DefineCPC}
]

add_routes(app, route_config)
