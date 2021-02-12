from pathlib import Path

port = 8501

base_dir = str((Path(__file__).parent / '../').resolve())
indexes_dir = base_dir + '/indexes/'
models_dir = base_dir + '/models/'
patents_dir = '/home/ubuntu/pqaidata/data/patents/'

mongo_host = 'localhost'
mongo_port = 27017
mongo_dbname = 'pqai'
mongo_pat_coll = 'bibliography'
mongo_npl_coll = 'npl'

index_selection_disabled = False
reranker_active = True
gpu_disabled = True

extensions = [
	'http://3.215.231.221:5000/extension/'
]
allow_outgoing_extension_requests = False
allow_incoming_extension_requests = False