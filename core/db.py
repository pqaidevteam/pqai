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
	abstract = patent['abstract']
	claims = '\n'.join(patent['claims'])
	desc = patent['description']
	desc = re.sub(r"\n+(?=[^A-Z])", ' ', desc)
	text = '\n'.join([abstract, claims, desc])
	return text


def get_cpcs (pn):
	patent = get_patent_data(pn)
	return patent.get('cpcs') if patent is not None else None
