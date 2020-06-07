
from pathlib import Path

base_dir = str((Path(__file__).parent / '../').resolve())
indexes_dir = base_dir + '/indexes/'
models_dir = base_dir + '/models/'
patents_dir = '/home/ubuntu/pqaidata/data/patents/'
mongo_host = 'localhost'
mongo_port = 27017
mongo_dbname = 'pqai'
mongo_pat_coll = 'bibliography'
mongo_npl_coll = 'npl'