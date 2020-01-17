from pymongo import MongoClient

from config.config import mongo_host, mongo_port, mongo_dbname, mongo_collname

client = MongoClient(mongo_host, mongo_port)
coll = client[mongo_dbname][mongo_collname]

def get_patent_data (pn):
	query = { 'publicationNumber': pn }
	patent_data = coll.find_one(query)
	return patent_data