import sys
from pathlib import Path
BASE_DIR = str(Path(__file__).parent.resolve())
sys.path.append(BASE_DIR)

from flask import request
from __main__ import app, create_request_and_serve
import api as API

@app.route('/suggest/cpcs', methods=['GET'])
def suggest_cpcs():
    return create_request_and_serve(request, API.SuggestCPCs)

@app.route('/predict/gaus', methods=['GET'])
def suggest_gaus():
    return create_request_and_serve(request, API.PredictGAUs)

@app.route('/suggest/synonyms', methods=['GET'])
def suggest_synonyms():
    return create_request_and_serve(request, API.SuggestSynonyms)

@app.route('/extract/concepts/', methods=['GET'])
def extract_concepts():
    return create_request_and_serve(request, API.ExtractConcepts)

@app.route('/definitions/cpcs/', methods=['GET'])
def define_cpc():
    return create_request_and_serve(request, API.DefineCPC)