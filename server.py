# Server
from flask import request
from flask_api import FlaskAPI, status, exceptions
from core.vectorizer import vectorize
from core.index import Index

app = FlaskAPI(__name__)


def b64decode(b64str):
    import base64
    return base64.b64decode(b64str).decode('utf-8')


@app.route('/indexes/<index_id>/patents/', methods=['GET'])
def search_index (index_id):
    n = request.args.get('n', 10, int)
    pn = request.args.get('pn', '', str)
    b64query = request.args.get('q', '', str)
    query = b64decode(b64query)

    if not pn and not query:
        return 'No search criteria in request.', status.HTTP_400_BAD_REQUEST
    if pn and query:
        return 'Invalid search criteria.', status.HTTP_400_BAD_REQUEST
    if pn:
        query_vector = vectorize(pn)
    if query:
        query_vector = vectorize(query)

    index = Index(index_id)
    matches = index.find_similar(query_vector, n)
    doc_ids = index.resolve_item_ids(matches)
    return doc_ids, status.HTTP_200_OK


@app.route('/patents/<pn>/snippet/', methods=['GET'])
def get_snippet(pn):
    return { snippet: True }, status.HTTP_200_OK


#     pn = request.data
#     tupl = get_index_by_id(indexid)
#     if tupl is None:
#         return json.dumps([])
#     patent_index, patent_list = tupl
#     n = 200  # number of results
#     plain_str = base64.b64decode(b64str).decode('utf-8')
#     vector = encode(plain_str)
#     sims, dists = patent_index.get_nns_by_vector(vector, int(n*1.5), 100000, True)
#     sims = [[patent_list[n], dists[i]] for i, n in enumerate(sims)]
#     sims = n_unique(sims, n)
#     return json.dumps(sims)


# # Find similar patents
# @app.route('/simpats/<indexid>/<b64str>', methods=['GET'])
# def simpats(b64str, indexid):
#     tupl = get_index_by_id(indexid)
#     if tupl is None:
#         return json.dumps([])
#     patent_index, patent_list = tupl
#     n = 100  # number of results
#     sp = base64.b64decode(b64str).decode('utf-8')   # subject patent
#     if not sp in patent_list:
#         return json.dumps([])
#     m = patent_list.index(sp)
#     vecs = []
#     while patent_list[m] == sp:                     # to cover all sentences
#         vecs.append(patent_index.get_item_vector(m))
#         m += 1
#     vecs = np.array(vecs)
#     resultant = vecs.sum(axis=0)
#     sims, dists = patent_index.get_nns_by_vector(resultant, 150, 100000, True)
#     sims = [[patent_list[n], dists[i]] for i, n in enumerate(sims)]
#     sims = n_unique(sims, n)
#     return json.dumps(sims)


# # Temporary route for benchmarking purposes
# @app.route('/longlist/<indexid>/<b64str>', methods=['GET'])
# def benchmark(b64str, indexid):
#     tupl = get_index_by_id(indexid)
#     if tupl is None:
#         return json.dumps([])
#     patent_index, patent_list = tupl
#     N = 100  # number of results
#     plain_str = base64.b64decode(b64str).decode('utf-8')
#     print(plain_str);
#     vector = encode(plain_str)
#     sims, dists = patent_index.get_nns_by_vector(vector, 200, 100000, True)
#     sims = [[patent_list[n], dists[i]] for i, n in enumerate(sims)]
#     sims = n_unique(sims, N)
#     print(len(sims));
#     return json.dumps(sims)


# @app.route('/snippet/', methods=['POST'])
# def get_snippet():
#     query = request.form['query']
#     pn = request.form['pn']
#     doc = mongo_coll.find_one({ 'publicationNumber': pn });
#     abstract = doc['abstract']
#     claims = '\n'.join(doc['claims'])
#     desc = doc['description']
#     desc = re.sub(r"\n+(?=[^A-Z])", ' ', desc)
#     text = '\n'.join([abstract, claims, desc])
#     snippet = generate_snippet(query, text, encode, highlight)
#     return snippet


# def confidence_score(vectors):
#     norms_squared = 0.00001 + (vectors * vectors).sum(axis=1, keepdims=True)
#     sims = np.dot(vectors, vectors.T) / norms_squared
#     std = np.std(sims.sum(axis=1, keepdims=False))
#     print('Confidence', str(std))
#     if std < 25:
#         return 'high'
#     elif std > 25 and std < 35:
#         return 'medium'
#     else:
#         return 'low'

# @app.route('/confidence/', methods=['POST'])
# def confidence():
#     cpcs = json.loads(request.form['cpcs'])
#     cpcs = [arr for arr in cpcs if len(arr) > 0]
#     vecs = np.array([avg_cpc_vec(arr) for arr in cpcs])
#     return confidence_score(vecs)


if __name__ == '__main__':
    app.run(debug=True)
