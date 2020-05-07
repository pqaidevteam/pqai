from pymongo import MongoClient
from operator import itemgetter
import json

from config.config import mongo_host, mongo_port, mongo_dbname, mongo_collname

client = MongoClient(mongo_host, mongo_port)
coll = client[mongo_dbname][mongo_collname]

def get_patent_data (pn, only_bib=False):
	"""Retrieve all of the patent's data from the database.
	
	Args:
	    pn (str): Publication number of the patent (with kind code).
	    	Must be exact match with the publication number stored
	    	in the database.
	    only_bib (bool, optional): Return only bibliography or full text
	    	including claims, description, etc.
	    	(Getting only the bibliography is faster.)
	
	Returns:
	    dict: The patent data, keys are patent fields, e.g.,
	    	`publicationNumber`, `filingDate`, `claims`, etc.
	    	If the patent is not found, `None` is returned.
	"""
	if only_bib:
		query = { 'publicationNumber': pn }
		patent_data = coll.find_one(query)
	else:
		path = f'/home/ubuntu/lts/data/patents/{pn}.json'
		with open(path) as file:
			patent_data = json.load(file)
	return patent_data


def get_full_text (pn):
	r"""Return abstract, claims, and description of the patent as a
	a single plain text string.
	
	Args:
	    pn (str): Publication number of the patent (with kind code).
	    	Must be exact match with the publication number stored
	    	in the database.
	
	Returns:
	    str: The full text (abstract + claims + description) all
	    	separated with newline (\n) characters.
	    	If patent is not found, `None` is returned.
	"""
	import re
	patent = get_patent_data(pn)
	if patent is None:
		return None
	abstract = patent['abstract']
	claims = '\n'.join(patent['claims'])
	desc = patent['description']
	desc = re.sub(r"\n+(?=[^A-Z])", ' ', desc)
	text = '\n'.join([abstract, claims, desc])
	return text


def get_cpcs (pn):
	"""Get list of CPC classes in which a patent is classified.
	
	Args:
	    pn (str): Publication number of the patent (with kind code).
	    	Must be exact match with the publication number stored
	    	in the database.
	
	Returns:
	    list: CPC codes, e.g., ['H04W52/02', 'H04W52/04']
	    	If patent is not found, `None` is returned.
	"""
	patent = get_patent_data(pn)
	if patent is None:
		return None
	return patent.get('cpcs') if patent is not None else None


def get_claims (pn):
	patent_data = get_patent_data(pn)
	if not patent_data:
		raise Exception(f'Patent number {pn} missing in database.')
	if not patent_data.get('claims'):
		raise Exception(f'Claims for {pn} missing in database.')
	return patent_data.get('claims')


def get_first_claim (pn):
	first_claim = get_claims(pn)[0]
	return first_claim