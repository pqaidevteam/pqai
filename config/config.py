import os
import sys
from pathlib import Path
from dotenv import load_dotenv
base_dir = str((Path(__file__).parent / '../').resolve())

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

env_file = f'{base_dir}/.env'
if os.path.isfile(env_file):
    load_dotenv(env_file)
    print('Created environment from .env file.')

if os.environ.get('TEST'):
    indexes_dir = f'{base_dir}/tests/test_indexes/'
    print('Application in test mode. Test indexes will be used.')
else:
    indexes_dir = f'{base_dir}/indexes/'

environment = os.environ.get('ENVIRONMENT')

use_faiss_indexes = bool(int(os.environ.get('USE_FAISS_INDEXES')))
use_annoy_indexes = bool(int(os.environ.get('USE_ANNOY_INDEXES')))
use_usearch_indexes = bool(int(os.environ.get('USE_USEARCH_INDEXES')))
load_usearch_indexes_in_memory = bool(int(os.environ.get('LOAD_USEARCH_INDEXES_IN_MEMORY')))

if not (use_faiss_indexes or use_annoy_indexes or use_usearch_indexes):
    print('Bad config! At least one index type must be activated.')
    sys.exit('App will now exit. Edit application config and try again')

models_dir = f'{base_dir}/models/'
docs_dir = f'{base_dir}/docs/'
tokens_file = os.environ.get('TOKENS_FILE')

smart_index_selection_active = bool(int(os.environ['SMART_INDEX_SELECTION']))
if os.environ.get('TEST'):
    smart_index_selection_active = True
if not smart_index_selection_active:
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

token_authentication_active = bool(int(os.environ['TOKEN_AUTHENTICATION']))

year_wise_indexes = bool(int(os.environ['YEAR_WISE_INDEXES']))
