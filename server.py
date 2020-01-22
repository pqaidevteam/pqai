# Server
from flask import request
import numpy as np
from flask_api import FlaskAPI, status, exceptions
from core.vectorizer import vectorize, CPCVectorizer
from core.indexes import get_index
from core.snippet import extract_snippet
from core.highlighter import highlight
from core import db
from core.gf import calc_confidence_score

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
    index = get_index(index_id)
    if index is None:
        return 'Index not found.', status.HTTP_500_INTERNAL_SERVER_ERROR
    
    hits = index.find_similar(query_vec, num_results, dist=True)
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

    # Add confidence score to results if needed
    # It is calculated on the basis of results' CPCs; if their vectors'
    # variance is low, score is high and vice versa
    if include_confidence_val:
        doc_ids = [doc_id for doc_id, dist in hits]
        cpcs = [db.get_cpcs(doc_id) for doc_id in doc_ids]
        vecs = np.array([CPCVectorizer().embed(arr) for arr in cpcs if arr])
        confidence_score = calc_confidence_score(vecs)
        for result in results:
            result['confidence'] = confidence_score

    # Add bibliography details to results if needed
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

    return results, status.HTTP_200_OK


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


if __name__ == '__main__':
    app.run(debug=True)
