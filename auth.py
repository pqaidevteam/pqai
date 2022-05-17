from config.config import tokens_file
import re
import os

def read_tokens():
    if not os.path.isfile(tokens_file):
        return set()
    with open(tokens_file, 'r') as f:
        lines = f.read().strip().splitlines()
        tokens = [re.split(r'\s+', line)[0] for line in lines]
    return set(tokens)

tokens = read_tokens()

def validate_access(request):
    route = request.base_url
    if not is_behind_auth(route):
        return True
    token = extract_token(request)
    return token in tokens

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