import os
import re
import logging
from logging.handlers import TimedRotatingFileHandler
from config.config import tokens_file
from fastapi import Request

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


def validate_access(request: Request):
    route = request.url.path
    if not is_behind_auth(route):
        return True

    token = extract_token(request)
    if token is None:
        logger.info("%s - No token", route)
        return False

    if token in TOKENS:
        logger.info("%s - Valid token: %s", route, token)
        return True

    read_tokens()  # Refresh token storage
    if token in TOKENS:
        logger.info("%s - Valid token: %s", route, token)
        return True

    logger.info("%s - Invalid token: %s", route, token)
    return False


def extract_token(req: Request):
    method = req.method
    if method == "GET":
        return req.query_params.get("token")
    if method == "POST":
        try:
            json_body = req.json()
            return json_body.get("token")
        except Exception as e:
            logger.error("Error extracting token from POST body: %s", e)
            return None
    return None


def is_behind_auth(route):
    if (
        route.endswith((".css", ".js", ".ico"))
        or "/drawings" in route
        or "/thumbnails" in route
        or "/docs" in route
    ):
        return False
    return True
