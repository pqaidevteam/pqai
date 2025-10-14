import json
import boto3
from pymongo import MongoClient
from .config import (
    MONGO_URI, MONGO_DBNAME, MONGO_PAT_COLL, MONGO_NPL_COLL,
    S3_CREDENTIALS, PQAI_S3_BUCKET_NAME, AWS_ACCESS_KEY_ID
)


class DocumentProxy:
    """
    A proxy that wraps raw document data and provides lazy-loading
    of expensive fields (from S3). Acts like a dict but fetches
    heavy data on-demand.
    """
    def __init__(self, doc_id, database, initial_data=None):
        self._id = doc_id
        self._db = database
        self._bib_data = initial_data or {}  # Fast data (MongoDB)
        self._full_data = None  # Heavy data (S3), loaded lazily
        self._full_loaded = False
    
    def get(self, key, default=None):
        """Get a field value, lazy-loading from S3 if necessary"""
        # Check if key is in bibliography data first
        if key in self._bib_data:
            return self._bib_data[key]
        
        # If requesting expensive fields, load full data
        if hasattr(self._db, 'EXPENSIVE_FIELDS') and key in self._db.EXPENSIVE_FIELDS:
            if not self._full_loaded:
                self._load_full_data()
            return self._full_data.get(key, default) if self._full_data else default
        
        return default
    
    def _load_full_data(self):
        """Lazy load full document from S3"""
        if not self._full_loaded:
            self._full_data = self._db._retrieve_full(self._id)
            self._full_loaded = True
            # Merge full data with bibliography data to have everything in one place
            if self._full_data:
                self._bib_data.update(self._full_data)
    
    def __getitem__(self, key):
        """Dict-like access with []"""
        result = self.get(key)
        if result is None:
            raise KeyError(key)
        return result
    
    def __contains__(self, key):
        """Support 'in' operator"""
        return key in self._bib_data or (
            hasattr(self._db, 'EXPENSIVE_FIELDS') and 
            key in self._db.EXPENSIVE_FIELDS
        )
    
    def keys(self):
        """Return available keys"""
        all_keys = set(self._bib_data.keys())
        if hasattr(self._db, 'EXPENSIVE_FIELDS'):
            all_keys.update(self._db.EXPENSIVE_FIELDS)
        return all_keys
    
    def __repr__(self):
        return f"DocumentProxy(id={self._id}, loaded={self._full_loaded})"


class PatentDatabase:
    # Define which fields require S3 access (expensive/slow)
    EXPENSIVE_FIELDS = {
        "claims", "description", "backwardCitations", 
        "forwardCitations", "examinersDetails", "cpcs"
    }
    
    # Define which fields are in MongoDB (fast)
    BIBLIOGRAPHY_FIELDS = {
        "publicationNumber", "title", "abstract", "url",
        "publicationDate", "filingDate", "priorityDate",
        "inventors", "assignees", "applicants"
    }
    
    def __init__(self, mongo_client=None, boto_client=None):
        self._mongo_client = mongo_client or MongoClient(MONGO_URI)
        self._boto_client = boto_client or (boto3.client("s3", **S3_CREDENTIALS) if AWS_ACCESS_KEY_ID else None)
        self._coll = self._mongo_client[MONGO_DBNAME][MONGO_PAT_COLL]
        # Keep _mongo_fields for backward compatibility with retrieve()
        self._mongo_fields = self.BIBLIOGRAPHY_FIELDS
    
    def get(self, pn):
        """
        Returns a DocumentProxy that lazy-loads expensive fields.
        Bibliography data loaded immediately from MongoDB (fast).
        Full data loaded on-demand from S3 (slow).
        
        This is the recommended API for new code.
        """
        # Always fetch bibliography from MongoDB first (fast)
        bib_data = self._retrieve_from_mongo(pn, list(self.BIBLIOGRAPHY_FIELDS))
        
        if bib_data is None:
            return None
        
        # Return proxy that will lazy-load S3 data when needed
        return DocumentProxy(pn, self, initial_data=bib_data)
    
    def _retrieve_full(self, pn):
        """Internal method to fetch full document from S3"""
        try:
            return self._retrieve_from_s3(pn)
        except Exception:
            return None
    
    def _has_full_data(self, pn):
        """Check if full data is available without loading it"""
        return self._boto_client is not None and pn.startswith("US")
    
    def retrieve(self, pn, fields=None):
        if fields and isinstance(fields, list):
            all_fields_in_mongo_db = not set(fields) - self._mongo_fields
            if all_fields_in_mongo_db:
                return self._retrieve_from_mongo(pn, fields)
        
        try:
            return self._retrieve_from_s3(pn)
        except Exception as e:
            if not fields: # If no specific fields requested, fallback to MongoDB
                return self._retrieve_from_mongo(pn)
            else:
                raise e
    
    def _retrieve_from_mongo(self, pn, fields=None):
        if fields and isinstance(fields, list):
            projection = {field: 1 for field in fields}
            projection["_id"] = 0
            return self._coll.find_one({"publicationNumber": pn}, projection)
        return self._coll.find_one({"publicationNumber": pn}, {"_id": 0})

    def _retrieve_from_s3(self, pn, fields=None):
        if self._boto_client and pn.startswith("US"):
            key = f"patents/{pn}.json"
            obj = self._boto_client.get_object(Bucket=PQAI_S3_BUCKET_NAME, Key=key)
            contents = obj["Body"].read().decode()
            doc = json.loads(contents)
            if fields and isinstance(fields, list):
                return {field: doc.get(field) for field in fields}
            return doc


class NPLDatabase:
    # NPL documents have no expensive fields - all data is in MongoDB
    EXPENSIVE_FIELDS = set()
    
    def __init__(self, mongo_client=None):
        self._mongo_client = mongo_client or MongoClient(MONGO_URI)
        self._collection = self._mongo_client[MONGO_DBNAME][MONGO_NPL_COLL]
    
    def get(self, doc_id):
        """
        Returns NPL document wrapped in DocumentProxy for consistency.
        All NPL data is in MongoDB, so no lazy loading needed.
        
        This is the recommended API for new code.
        """
        data = self._collection.find_one({"id": doc_id}, {"_id": 0})
        if data:
            return DocumentProxy(doc_id, self, initial_data=data)
        return None
    
    def _retrieve_full(self, doc_id):
        """NPL has no separate full data - everything is in MongoDB"""
        return None
    
    def retrieve(self, doc_id):
        """Legacy method for backward compatibility"""
        return self._collection.find_one({"id": doc_id}, {"_id": 0})
