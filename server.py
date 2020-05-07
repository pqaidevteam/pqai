# Server
from flask import request
import numpy as np
from flask_api import FlaskAPI, status, exceptions
from core.vectorizer import vectorize, CPCVectorizer, DistilBERTVectorizer, SIFTextVectorizer
from core.indexes import get_index
from core.indexes import index_ids as available_indexes
from core.snippet import extract_snippet, map_elements_to_text
from core.highlighter import highlight
from core import db
from core import datasets
from core.utils import calc_confidence_score, get_paragraphs
from core import searcher

app = FlaskAPI(__name__)

@app.route('/documents/', methods=['GET'])
def search_index ():
    num_results = request.args.get('n', 10, int)
    index_id = request.args.get('idx', '', str)
    doc_id = request.args.get('pn', '', str)
    query = request.args.get('q', '', str)
    include_confidence_val = request.args.get('cnfd', 0, int)
    include_bib_details = request.args.get('bib', 0, int)
    include_distances = request.args.get('dist', 1, int)
    include_snippets = request.args.get('snip', 0, int)

    if not index_id:
        return 'No index specified for search.', status.HTTP_400_BAD_REQUEST
    if not (doc_id or query):
        return 'No search criteria in request.', status.HTTP_400_BAD_REQUEST
    if doc_id and query:
        return 'Invalid search criteria.', status.HTTP_400_BAD_REQUEST
    if doc_id and not query:
        query = doc_id

    query_vec = vectorize(query)
    if query_vec is None:
        return 'Problematic query.', status.HTTP_500_INTERNAL_SERVER_ERROR
    
    """
    If automatic index selection mode is enabled by setting `index_id`
    to `auto`, indexes will be predicted
    """ 
    indexes = None if index_id == 'auto' else [index_id]
    try:
        hits = searcher.search(query, num_results, indexes)
    except:
        return 'Error while searching.', status.HTTP_500_INTERNAL_SERVER_ERROR 
    
    if hits is None:
        return 'Error while searching.', status.HTTP_500_INTERNAL_SERVER_ERROR
    
    # The results array will carry one `dict` per result. Depending on
    # the fields requested by the client, data will be added to the
    # dictionaries
    if include_distances:
        results = [{'publicationNumber': doc_id, 'distance': dist}
                    for doc_id, dist in hits]
    else:
        results = [{'publicationNumber': doc_id} for doc_id, dist in hits]

    # Add confidence score to results if requested
    # It is calculated on the basis of results' CPCs; if their vectors'
    # variance is low, score is high and vice versa
    if include_confidence_val:
        doc_ids = [doc_id for doc_id, dist in hits]
        cpcs = [db.get_cpcs(doc_id) for doc_id in doc_ids]
        vecs = np.array([CPCVectorizer().embed(arr) for arr in cpcs if arr])
        confidence_score = calc_confidence_score(vecs)
        for result in results:
            result['confidence'] = confidence_score

    # Add bibliography details to results if requested
    if include_bib_details:
        for result in results:
            patent = db.get_patent_data(result['publicationNumber'])
            for field in ('title', 'abstract', 'filingDate'):
                result[field] = patent[field]
            if not patent.get('applicants'):
                result['assignee'] = ''
            else:
                result['assignee'] = patent['applicants'][0]

    if include_snippets:
        for result in results:
            text = db.get_full_text(result['publicationNumber'])
            snippet = extract_snippet(query, text)
            result['snippet'] = snippet

    response = {
        'results': results,
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
    text = db.get_full_text(pn)
    snippet = extract_snippet(query, text)
    response = dict(
        publicationNumber = pn,
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
    
    elements = get_paragraphs(query)

    ref_data = db.get_patent_data(ref)
    target_text = ref_data['description']
    # arr_vectorize = DistilBERTVectorizer().embed_arr
    embed = SIFTextVectorizer().embed
    arr_vectorize = lambda X: [embed(x) for x in X]

    mapping = map_elements_to_text (elements, target_text, arr_vectorize)
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


if __name__ == '__main__':
    app.run(debug=True)
