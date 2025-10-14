import re

def is_patent_number(pn):
    """Check if a string is a patent number (starts with 2 uppercase letters)"""
    return bool(re.match(r"^[A-Z]{2}", pn))

def normalize_patent_number_for_mongodb(pn):
    if pn.startswith("US") and len(pn) == 15:
        pn = pn[:6] + pn[7:]
    return pn

def normalize_patent_number_for_s3(pn):
    if pn.startswith("US") and len(pn) == 14:
        pn = pn[:6] + "0" + pn[6:]
    return pn