from .databases import PatentDatabase, NPLDatabase
from .utils import is_patent_number
import re

# Singleton instances - RECOMMENDED API
patent_db = PatentDatabase()
npl_db = NPLDatabase()

# Legacy constants for backward compatibility
BIBLIOGRAPHY_FIELDS = [
    "publicationNumber",
    "title",
    "abstract",
    "publicationDate",
    "filingDate",
    "priorityDate",
    "inventors",
    "assignees"
]

# Legacy functions for backward compatibility
# New code should use patent_db.get() and npl_db.get() instead

def get_patent_data(pn, only_bib=False):
    if only_bib:
        return patent_db.retrieve(pn, fields=BIBLIOGRAPHY_FIELDS)
    return patent_db.retrieve(pn)

def get_document(doc_id):
    if is_patent_number(doc_id):
        return patent_db.retrieve(doc_id, fields=BIBLIOGRAPHY_FIELDS)
    else:
        return npl_db.retrieve(doc_id)

def get_documents(doc_ids):
    patents = []
    npls = []
    for doc_id in doc_ids: # TODO: Optimize this to batch fetch from DBs
        if is_patent_number(doc_id):
            patents.append(doc_id)
        else:
            npls.append(doc_id)

    results = {}
    for pn in patents:
        results[pn] = patent_db.retrieve(pn, fields=BIBLIOGRAPHY_FIELDS)

    for doc_id in npls:
        results[doc_id] = npl_db.retrieve(doc_id)

    return [results.get(doc_id) for doc_id in doc_ids]

def get_full_text(pn):
    patent = patent_db.retrieve(pn, ["abstract", "claims", "description"])
    if patent is None:
        return None
    abstract = patent["abstract"]
    claims = "\n".join(patent["claims"])
    desc = patent["description"]
    desc = re.sub(r"\n+(?=[^A-Z])", " ", desc)  # collapse multiple line breaks
    text = "\n".join([abstract, claims, desc])
    return text
