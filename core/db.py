from pymongo import MongoClient
from operator import itemgetter

from config.config import mongo_host, mongo_port, mongo_dbname, mongo_collname

client = MongoClient(mongo_host, mongo_port)
coll = client[mongo_dbname][mongo_collname]

def get_patent_data (pn):
	query = { 'publicationNumber': pn }
	patent_data = coll.find_one(query)
	return patent_data

def get_full_text (pn):
	import re
	patent = get_patent_data(pn)
	if patent is None:
		return None

	abst, clms, desc = itemgetter('abstract', 'claims', 'description')(patent)
	clms = '\n'.join(clms)
	desc = re.sub(r"\n+(?=[^A-Z])", ' ', desc)
	text = '\n'.join([abst, clms, desc])
	return text