from core import utils
from core import db
from core.indexes import index_ids as AVAILABLE_INDEXES
from core.indexes import get_index
from core.vectorizer import vectorize
from core.subclass_predictor import predict_subclasses
from dateutil.parser import parse as parse_date

N_INDEXES_TO_SEARCH = 3
MAX_RESULTS_LIMIT = 100


def is_published_before (before, pn):
	if before is None:
		return True
	date = db.get_patent_data(pn)['publicationDate']
	return parse_date(before) > parse_date(date)


def is_published_after (after, pn):
	if after is None:
		return True
	date = db.get_patent_data(pn)['publicationDate']
	return parse_date(after) < parse_date(date)


def filter_by_date (results, before, after):
	return [result for result in results
				if is_published_before(before, result[0])
				and is_published_after(after, result[0])]

def filter_family_members (results):
	return [results[0]] + [results[i] for i in range(1,len(results))
							if results[i][1] != results[i-1][1]]


def search_by_patent_number (pn, n=10, indexes=None, before=None, after=None):
	try:
		first_claim = db.get_first_claim(pn)
	except:
		raise Exception(f'Claim cannot be retrieved for {pn}')

	claim_text = utils.remove_claim_number(first_claim)
	return search_by_text_query(claim_text, n, indexes, before, after)


def search_by_text_query (query_text, n=10, indexes=None, before=None, after=None):
	if not (type(indexes) == list and len(indexes) > 0):
		indexes = predict_subclasses(query_text,
								N_INDEXES_TO_SEARCH,
								AVAILABLE_INDEXES)

	query_vector = vectorize(query_text)

	m = n
	results = []
	while len(results) < n and m <= MAX_RESULTS_LIMIT:
		results = []
		for index_id in indexes:
			index = get_index(index_id)
			res = index.find_similar(query_vector, m, dist=True)
			results += res

		DIST_IDX = 1
		results.sort(key=lambda x: x[DIST_IDX])
		results = filter_by_date(results, before, after)
		results = filter_family_members(results)
		m *= 2
	
	return results[:n]


def search (value, n=10, indexes=None, before=None, after=None):
	if utils.is_patent_number(value):
		return search_by_patent_number(value, n, indexes, before, after)
	else:
		return search_by_text_query(value, n, indexes, before, after)

