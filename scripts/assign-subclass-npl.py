"""
Associate CPC subclasses to NPL documents in MongoDB
"""
import os
import sys
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv
from tqdm import tqdm

BASE_DIR = str(Path(__file__).parent.parent.resolve())
ENV_FILE = f"{BASE_DIR}/.env"
load_dotenv(ENV_FILE)

print(BASE_DIR)
sys.path.append(BASE_DIR)
from core.classifiers import BERTSubclassPredictor

MONGO_PORT = os.environ.get("MONGO_PORT", "27017")
MONGO_HOST = os.environ.get("MONGO_HOST", "localhost")
MONGO_DBNAME = os.environ.get("MONGO_DBNAME", "pqai")
MONGO_NPL_COLL = os.environ.get("MONGO_NPL_COLL", "npl")
ABSTRACT_FIELD = "paperAbstract"

client = MongoClient(f"mongodb://{MONGO_HOST}:{MONGO_PORT}")
coll = client[MONGO_DBNAME][MONGO_NPL_COLL]

model = BERTSubclassPredictor()

N = coll.count()
cursor = coll.find()
for _ in tqdm(range(N)):
    doc = cursor.next()
    subclass = doc.get("subsclass")
    if isinstance(subclass, str) and len(subclass) == 4:
        continue
    doc_id = doc["id"]
    abstract = doc[ABSTRACT_FIELD]
    predictions = model.predict_subclasses(abstract)
    top_prediction = predictions[0]
    match = {"id": doc_id}
    update = {"$set": {"subclass": top_prediction}}
    coll.update_one(match, update)
