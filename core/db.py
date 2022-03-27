from pymongo import MongoClient
from operator import itemgetter
import json

from config.config import mongo_uri
from config.config import mongo_dbname, mongo_pat_coll, mongo_npl_coll

from config.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
import boto3
import botocore.exceptions
botoclient = boto3.client('s3',
						  aws_access_key_id=AWS_ACCESS_KEY_ID,
						  aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
from config.config import PQAI_S3_BUCKET_NAME

client = MongoClient(mongo_uri)
pat_coll = client[mongo_dbname][mongo_pat_coll]
npl_coll = client[mongo_dbname][mongo_npl_coll]

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
		patent_data = pat_coll.find_one(query)
		return patent_data
	else:
		try:
			bucket = PQAI_S3_BUCKET_NAME
			key = f'patents/{pn}.json'
			obj = botoclient.get_object(Bucket=bucket, Key=key)
			contents = obj["Body"].read().decode()
			return json.loads(contents)
		except botocore.exceptions.ClientError:
		    return None

def get_bibliography(pn):
	return get_patent_data(pn, only_bib=True)

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


def get_document (doc_id):
	if len(doc_id) == 40:
		return npl_coll.find_one({ 'id': doc_id })
	else:
		return pat_coll.find_one({ 'publicationNumber': doc_id })