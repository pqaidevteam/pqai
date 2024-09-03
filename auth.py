import os
import re
import logging
from logging.handlers import TimedRotatingFileHandler
from config.config import tokens_file

logger = logging.getLogger('API-ACCESS')
logger.setLevel(logging.DEBUG)

fh = TimedRotatingFileHandler(
    'api-access.log',
    when='midnight',
    interval=1,
    backupCount=7
)
fh.setLevel(logging.INFO)
fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(fh)

TOKENS = set()

def read_tokens():
    global TOKENS
    if not os.path.isfile(tokens_file):
        return set()
    with open(tokens_file, "r", encoding="utf-8") as f:
        lines = f.read().strip().splitlines()
        tokens = [re.split(r'\s+', l)[0] for l in lines if l.strip()]
        TOKENS = TOKENS.union(tokens)

def validate_access(request):
    route = request.path
    if not is_behind_auth(route):
        return True
    token = extract_token(request)
    if token is None:
        logger.info("%s - No token", route)
        return False
    
    if token in TOKENS:
        logger.info("%s - Valid token: %s", route, token)
        return True
    
    read_tokens() # to account for tokens added after server started
    if token in TOKENS:
        logger.info("%s - Valid token: %s", route, token)
        return True
    logger.info("%s - Invalid token: %s", route, token)
    return False

def extract_token(req):
    method = req.method
    if method == 'GET':
        return req.args.to_dict().get('token')
    if method == 'POST' and req.json:
        return req.json.get('token')
    return None

def is_behind_auth(route):
    if route.endswith(('.css', '.js', '.ico')) \
        or '/drawings' in route \
        or '/thumbnails' in route \
        or '/docs' in route:
        return False
    return True
