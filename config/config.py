from pathlib import Path
import os
import sys
base_dir = str((Path(__file__).parent / '../').resolve())

env_file = f'{base_dir}/.env'
if os.path.isfile(env_file):
    from dotenv import load_dotenv
    load_dotenv(env_file)
    print('Created environment from .env file.')

if os.environ.get('TEST'):
    indexes_dir = f'{base_dir}/tests/test_indexes/'
    print('Application in test mode. Test indexes will be used.')
else:
    indexes_dir = f'{base_dir}/indexes/'

use_faiss_indexes = bool(int(os.environ.get('USE_FAISS_INDEXES')))
use_annoy_indexes = bool(int(os.environ.get('USE_ANNOY_INDEXES')))

if not (use_faiss_indexes or use_annoy_indexes):
    print('Bad config! At least one index type must be activated.')
    sys.exit('App will now exit. Edit application config and try again')

models_dir = f'{base_dir}/models/'
docs_dir = f'{base_dir}/docs/'
tokens_file = f'{base_dir}/tokens.txt'

mongo_host = os.environ['MONGO_HOST']
mongo_port = int(os.environ['MONGO_PORT'])
mongo_dbname = os.environ['MONGO_DBNAME']
mongo_pat_coll = os.environ['MONGO_PAT_COLL']
mongo_npl_coll = os.environ['MONGO_NPL_COLL']

index_selection_disabled = not bool(int(os.environ['SMART_INDEX_SELECTION']))
if os.environ.get('TEST'):
    index_selection_disabled = True
if index_selection_disabled:
    print('WARNING: Index selection is inactive. Search may be slow.')

reranker_active = bool(int(os.environ['USE_RERANKER']))
gpu_disabled = bool(int(os.environ['DISABLE_GPU']))
if gpu_disabled:
    print('Application has been configured to run without GPU.')
else:
    print('Application will use GPU if available.')

extensions = []
allow_outgoing_extension_requests = bool(int(os.environ['OUTGOING_EXT']))
allow_incoming_extension_requests = bool(int(os.environ['INCOMING_EXT']))
if allow_incoming_extension_requests:
    print('Server has been configured to accept extension requests.')

port = int(os.environ['API_PORT'])
PQAI_S3_BUCKET_NAME = os.environ['PQAI_S3_BUCKET_NAME']
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
sentry_url = os.environ.get('SENTRY_URL')

token_authentication_active = bool(int(os.environ['TOKEN_AUTHENTICATION']))
