#  This script will read NPL document data from the source JSON file
#  and will create a MongoDB collection `pqai.npl` containing those
#  documents. These documents are required for testing.
#  If the collection already exists with the required documents, this
#  script will have no effect.

import json
from pathlib import Path
from tqdm import tqdm
from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "pqai"
COLL_NAME = "npl"
TEST_DIR = str(Path(__file__).parent.resolve())
SOURCE_FILE = f'{TEST_DIR}/test_npl_docs.json'

TEST_DIR = str(Path(__file__).parent.resolve())

with open(SOURCE_FILE, 'r') as f:
    docs = json.load(f)
    assert len(docs) > 0

    client = MongoClient(MONGO_URI)
    coll = client[DB_NAME][COLL_NAME]
    
    print("Adding documents to Mongo DB")
    for doc in tqdm(docs, ncols=80, desc="Progress"):
        doc_id = doc["id"]
        if coll.find_one({"id": doc_id}):
            continue
        result = coll.insert_one(doc)
        assert result.acknowledged
