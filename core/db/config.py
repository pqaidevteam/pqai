import os

MONGO_URI = os.environ.get("MONGO_URI") or "mongodb://localhost:27017"
MONGO_DBNAME = os.environ.get("MONGO_DBNAME") or "pqai"
MONGO_PAT_COLL = os.environ.get("MONGO_PAT_COLL") or "patents"
MONGO_NPL_COLL = os.environ.get("MONGO_NPL_COLL") or "npl"

AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
PQAI_S3_BUCKET_NAME = os.environ["PQAI_S3_BUCKET_NAME"]

S3_CREDENTIALS = {
    "aws_access_key_id": AWS_ACCESS_KEY_ID,
    "aws_secret_access_key": AWS_SECRET_ACCESS_KEY,
}
