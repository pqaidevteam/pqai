from pathlib import Path
import os
base_dir = str((Path(__file__).parent / '../').resolve())

env_file = f'{base_dir}/.env'
if os.path.isfile(env_file):
    from dotenv import load_dotenv
    load_dotenv(env_file)

indexes_dir = f'{base_dir}/indexes/'
models_dir = f'{base_dir}/models/'
docs_dir = f'{base_dir}/docs/'
tokens_file = f'{base_dir}/tokens.txt'

mongo_host = os.environ['MONGO_HOST']
mongo_port = int(os.environ['MONGO_PORT'])
mongo_dbname = os.environ['MONGO_DBNAME']
mongo_pat_coll = os.environ['MONGO_PAT_COLL']
mongo_npl_coll = os.environ['MONGO_NPL_COLL']

index_selection_disabled = True
reranker_active = True
gpu_disabled = True

extensions = []
allow_outgoing_extension_requests = False
allow_incoming_extension_requests = False

port = int(os.environ['API_PORT'])
PQAI_S3_BUCKET_NAME = os.environ['PQAI_S3_BUCKET_NAME']
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
sentry_url = os.environ.get('SENTRY_URL')