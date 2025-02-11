import sys
from pathlib import Path
BASE_DIR = str(Path(__file__).parent.resolve())
sys.path.append(BASE_DIR)

import api as API

route_config = [
    {
        "method": "GET",
        "path": "/suggest/cpcs",
        "handler": API.SuggestCPCs,
        "rateLimit": 5,
        "protected": True
    },
    {
        "method": "GET",
        "path": "/predict/gaus",
        "handler": API.PredictGAUs,
        "rateLimit": 5,
        "protected": True
    },
    {
        "method": "GET",
        "path": "/suggest/synonyms",
        "handler": API.SuggestSynonyms,
        "rateLimit": 5,
        "protected": True
    },
    {
        "method": "GET",
        "path": "/extract/concepts",
        "handler": API.ExtractConcepts,
        "rateLimit": 5,
        "protected": True
    },
    {
        "method": "GET",
        "path": "/definitions/cpcs",
        "handler": API.DefineCPC,
        "rateLimit": -1,
        "protected": True
    }
]
