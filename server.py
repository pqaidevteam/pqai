# Server
from flask import request
from flask_api import FlaskAPI, status, exceptions

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

import re
import numpy as np
from core.vectorizer import SIFTextVectorizer
from core.indexes import get_index
from core.indexes import index_ids as available_indexes
from core.snippet import extract_snippet, map_elements_to_text
from core.highlighter import highlight
from core import db
from core import datasets
from core import utils
from core import searcher
from core.documents import Document
from core.reranking import MatchPyramidRanker
from core.remote import search_extensions, merge_results
from config.config import reranker_active, allow_outgoing_extension_requests
from core.reranking import CustomRanker

reranker = CustomRanker()

app = FlaskAPI(__name__)

# TODO
# Find an appropriate location for this function and move it there
def get_element_wise_mapping(query, doc):
    if utils.is_patent_number(query): 
        elements = utils.get_elements(db.get_first_claim(query))
    else:
        elements = utils.get_elements(query)
    target_text = doc.full_text
    embed = SIFTextVectorizer().embed
    arr_vectorize = lambda X: [embed(x) for x in X]
    mapping = map_elements_to_text(elements, target_text, arr_vectorize)
    return mapping


@app.route('/documents/', methods=['GET'])
def search_index (extend=True):
    num_results = request.args.get('n', 10, int)
    index_id = request.args.get('idx', '', str)
    query = request.args.get('q', '', str)
    before = request.args.get('before', '', str)
    after = request.args.get('after', '', str)
    include_snippets = request.args.get('snip', 0, int)
    include_mappings = request.args.get('maps', 0, int)
    
    # If automatic index selection mode is enabled by setting
    # `index_id` to `auto`, indexes will be predicted
    indexes = None if index_id == 'auto' else [index_id]

    before = before if before else None
    after = after if after else None

    if reranker_active:
        global reranker
        if reranker is None:
            reranker = MatchPyramidRanker()
    else:
        reranker = None

    try:
        results = searcher.search(query, num_results, indexes, before, after, reranker)
    except Exception as e:
        print(repr(e))
        return 'Error while searching.', status.HTTP_500_INTERNAL_SERVER_ERROR 
    
    if results is None:
        return 'Error while searching.', status.HTTP_500_INTERNAL_SERVER_ERROR

    if include_snippets:
        for result in results:
            snippet = extract_snippet(query, result.full_text)
            result.snippet = snippet

    if (not extend) or include_mappings:
        for result in results:
            mapping = get_element_wise_mapping(query, result)
            result.mapping = mapping

    if extend and allow_outgoing_extension_requests:
        remote_results = search_extensions(request.args)
        results = merge_results([results, remote_results])

    response = {
        'results': [result.to_json() for result in results],
        'query': query,
        'index': index_id
    }
    return response, status.HTTP_200_OK


@app.route('/snippets/', methods=['GET'])
def get_snippet():
    query = request.args.get('q', '', str)
    pn = request.args.get('pn', '', str)
    if not (pn or query):
        return 'Document id or query invalid.', status.HTTP_400_BAD_REQUEST
    
    doc = Document(pn)
    snippet = extract_snippet(query, doc.full_text)
    response = dict(
        publication_id = pn,
        snippet = snippet,
        query = query
    )
    return response, status.HTTP_200_OK


@app.route('/mappings/', methods=['GET'])
def get_mapping():
    query = request.args.get('q', '', str)
    ref = request.args.get('ref', '', str)
    if not (ref or query):
        return 'Reference or query invalid.', status.HTTP_400_BAD_REQUEST
    
    doc = Document(ref)
    mapping = get_element_wise_mapping(query, doc)
    return mapping, status.HTTP_200_OK


@app.route('/datasets/', methods=['GET'])
def get_datapoint():
    dataset = request.args.get('dataset', '', str)
    n = request.args.get('n', 1, int)
    if not dataset or n < 1:
        return 'Invalid query.', status.HTTP_400_BAD_REQUEST

    if dataset.lower() == 'poc':
        poc = datasets.PoC()
        datapoint = poc.get_datapoint(n,  fields=[
            'publicationNumber', 'title', 'abstract'])
    else:
        datapoint = {}

    return datapoint, status.HTTP_200_OK

@app.route('/extension/', methods=['GET'])
def handle_extension_request():
    return search_index (extend=False)


if __name__ == '__main__':
    app.run(debug=False, threaded=False)
