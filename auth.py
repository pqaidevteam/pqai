import os
import re
from config.config import tokens_file

TOKENS = set()

def read_tokens():
    global TOKENS
    if not os.path.isfile(tokens_file):
        return set()
    with open(tokens_file, 'r') as f:
        lines = f.read().strip().splitlines()
        tokens = [re.split(r'\s+', l)[0] for l in lines if l.strip()]
        TOKENS = TOKENS.union(tokens)

def validate_access(request):
    route = request.base_url
    if not is_behind_auth(route):
        return True
    token = extract_token(request)
    if token is None:
        return False
    if token in TOKENS:
        return True
    read_tokens() # to account for tokens added after server started
    return token in TOKENS

def extract_token(req):
    method = req.method
    if method == 'GET':
        return req.args.to_dict().get('token')
    elif method == 'POST' and req.json:
        return req.json.get('token')
    else:
        return None

def is_behind_auth(route):
    if route.endswith(('.css', '.js', '.ico')) \
        or '/drawings' in route \
        or '/thumbnails' in route \
        or '/docs' in route:
        return False
    return True
