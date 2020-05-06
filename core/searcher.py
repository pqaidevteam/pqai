from core import utils
from core import db
from core.indexes import index_ids as AVAILABLE_INDEXES
from core.indexes import get_index
from core.vectorizer import vectorize
from core.subclass_predictor import predict_subclasses

N_INDEXES_TO_SEARCH = 3

def search_by_patent_number (pn, n=10, before=None, after=None):
	patent_data = db.get_patent_data(pn)
	if not patent_data:
		raise Exception(f'Patent number {pn} missing in database.')
	if not patent_data.get('claims'):
		raise Exception(f'Claims for {pn} missing in database.')
	
	first_claim = patent_data['claims'][0]
	claim_text = utils.remove_claim_number(first_claim)
	return search_by_text_query(claim_text, n, before, after)


def search_by_text_query (query_text, n=10, before=None, after=None):
	selected_indexes = predict_subclasses(
									query_text,
									N_INDEXES_TO_SEARCH,
									AVAILABLE_INDEXES)

	query_vector = vectorize(query_text)

	results = []
	for index_id in selected_indexes:
		index = get_index(index_id)
		res = index.find_similar(query_vector, n, dist=True)
		results += res

	SCORE = 1
	results.sort(key=lambda x: x[SCORE])
	return results[:n]


def search (value, n=10, before=None, after=None):
	if utils.is_patent_number(value):
		return search_by_patent_number(value, n, before, after)
	else:
		return search_by_text_query(value, n, before, after)

