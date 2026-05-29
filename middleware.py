import os
import re
import time
import asyncio
from datetime import datetime
from collections import deque
import logging
from logging.handlers import TimedRotatingFileHandler
from pymongo import MongoClient

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.routing import compile_path

from config import config
from routes import routes_config

logger = logging.getLogger('API-ACCESS')
logger.setLevel(logging.DEBUG)

fh = TimedRotatingFileHandler(
    'api-access.log',
    when='midnight',
    interval=1,
    backupCount=31
)
fh.setLevel(logging.INFO)
fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(fh)

MONGO_HOST = os.environ["MONGO_HOST"]
MONGO_PORT = os.environ["MONGO_PORT"]
MONGO_USER = os.environ["MONGO_USER"]
MONGO_PASSWORD = os.environ["MONGO_PASSWORD"]
if MONGO_USER and MONGO_PASSWORD:
    MONGO_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}"
else:
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}"

MONGO_CLIENT = MongoClient(MONGO_URI)
TOKENS_COLL = MONGO_CLIENT["pqai"]["users"]
USAGE_COLL = MONGO_CLIENT["pqai"]["usage"]


class TokenRegistry:
    DEFAULT_QUOTA = int(os.environ.get('DEFAULT_USAGE_QUOTA', 50))
    
    def __init__(self, tokens_file):
        self.tokens_file = tokens_file
        self.token_quotas = {}
        self.load_all_tokens()
    
    def load_all_tokens(self):
        if os.path.isfile(self.tokens_file):
            with open(self.tokens_file, "r", encoding="utf-8") as f:
                lines = f.read().strip().splitlines()
                lines = [l for l in lines if not l.startswith("#") and l.strip()]
                
                for line in lines:
                    parts = re.split(r'\s+', line)
                    token = parts[0]
                    if len(parts) >= 2 and parts[1].isdigit():
                        quota = int(parts[1])
                    else:
                        quota = self.DEFAULT_QUOTA
                    self.token_quotas[token] = quota
        
        try:
            mongo_tokens = TOKENS_COLL.find({"apiKey": {"$exists": True}})
            for doc in mongo_tokens:
                token = doc.get("apiKey")
                if token and token not in self.token_quotas:
                    quota = doc.get("quota", self.DEFAULT_QUOTA)
                    self.token_quotas[token] = quota
            logger.info("Loaded %d tokens with quotas", len(self.token_quotas))
        except Exception as e:
            logger.error("Error reading tokens from MongoDB: %s", e)
    
    def has_token(self, token):
        return token in self.token_quotas
    
    def get_quota(self, token):
        return self.token_quotas.get(token)


token_registry = TokenRegistry(config.tokens_file)


class CustomLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        ip = request.client.host
        route = request.url.path

        t0 = datetime.now()
        response = await call_next(request)
        dt = (datetime.now() - t0).total_seconds()

        log_message = (
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
            f"{ip} "
            f"{request.method} "
            f"{route} "
            f"{response.status_code} "
            f"{dt:.2f}s"
        )
        logger.info(log_message)
        return response


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        if not config.token_authentication_active:
            return await call_next(request)

        route = request.url.path

        route_config = self.match_route(route, routes_config)
        if not route_config:
            return await call_next(request)
        
        is_protected = route_config.get("protected", True)
        if not is_protected:
            return await call_next(request)

        token = await self.extract_token(request)
        if token is None:
            logger.info("%s - No token", route)
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized"}
            )

        if not token_registry.has_token(token):
            logger.info("%s - Invalid token", route)
            return JSONResponse(
                status_code=401,
                content={"detail": "Unauthorized"}
            )

        logger.info("%s - Valid token: %s", route, token)
        return await call_next(request)

    @staticmethod
    def match_route(route: str, routes_config: list):
        for r in routes_config:
            route_regex, *_ = compile_path(r["path"])
            if route_regex.match(route):
                return r
        return None

    @staticmethod
    async def extract_token(req: Request):
        auth_header = req.headers.get("Authorization")
        if auth_header:
            if auth_header.startswith("Bearer "):
                return auth_header[7:].strip()
            return auth_header.strip()
        
        method = req.method
        if method == "GET":
            return req.query_params.get("token")
        if method == "POST":
            try:
                json_body = await req.json()
                return json_body.get("token")
            except Exception as e:
                logger.error("Error extracting token from POST body: %s", e)
                return None
        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, default_limit: int, window: int, routes_limits: dict = None):
        super().__init__(app)
        self.default_limit = default_limit  # request volume per time window per client
        self.window = window  # window duration in seconds
        self.request_log = {}  # tracks request counts
        self.lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next):
        route = request.url.path
        route_config = next((r for r in routes_config if r["path"] == route), None)

        if route_config is None:
            return await call_next(request)

        limit = route_config.get("rateLimit", self.default_limit)
        if limit == -1:
            return await call_next(request)
        
        # Use token if available, otherwise use IP address to enforce rate limits
        client_id = await AuthMiddleware.extract_token(request)
        if client_id is None:
            client_id = request.client.host
        
        current_time = time.monotonic()
        key = (client_id, route)

        async with self.lock:
            request_times = self.request_log.setdefault(key, deque())

            while request_times and request_times[0] <= current_time - self.window:
                request_times.popleft()

            if len(request_times) >= limit:
                retry_after = self.window - (current_time - request_times[0])
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests"},
                    headers={"Retry-After": str(int(retry_after))}
                )

            request_times.append(current_time)

            # Clean up to prevent memory leak
            if not request_times:
                del self.request_log[key]

        return await call_next(request)


class QuotaMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.lock = asyncio.Lock()
    
    async def dispatch(self, request: Request, call_next):
        if not config.token_authentication_active:
            return await call_next(request)
        
        route = request.url.path
        
        # Check if this route is metered (requests counted against quota)
        route_config = AuthMiddleware.match_route(route, routes_config)
        if not route_config or not route_config.get('metered', False):
            return await call_next(request)
        
        token = await AuthMiddleware.extract_token(request)
        if token is None:
            return await call_next(request)
        
        token_quota = token_registry.get_quota(token)
        if token_quota is None:
            return await call_next(request)
        
        current_time = datetime.now()
        current_month_start = datetime(current_time.year, current_time.month, 1)
        
        async with self.lock:
            current_usage = USAGE_COLL.count_documents({
                "apiKey": token,
                "timestamp": {"$gte": current_month_start}
            })
            
            if current_usage >= token_quota:
                logger.info(
                    "%s - Quota exceeded for token %s (%d/%d requests used)",
                    route, token, current_usage, token_quota
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Monthly search quota exceeded",
                        "quota_limit": token_quota,
                        "quota_used": current_usage,
                        "quota_reset": "Monthly on the 1st"
                    }
                )
        
        response = await call_next(request)
        
        if 200 <= response.status_code < 300: # only successful requests count against quota
            async with self.lock:
                USAGE_COLL.insert_one({
                    "apiKey": token,
                    "timestamp": current_time,
                    "route": route,
                    "status": response.status_code
                })
                
                logger.info(
                    "%s - Quota counted for token %s: %d/%d requests used (status: %d)",
                    route, token, current_usage + 1, token_quota, response.status_code
                )
        
        return response
