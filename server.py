import os
import json
import importlib
import logging

from functools import partial

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.routing import Route

from config import config
from routes import routes_config
import core.api as API
from middleware import CustomLogMiddleware, AuthMiddleware, RateLimitMiddleware

if config.gpu_disabled:
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

logger = logging.getLogger("api_requests")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)

app = FastAPI(openapi_url=None, docs_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(CustomLogMiddleware)
app.add_middleware(AuthMiddleware, tokens_file=config.tokens_file)
app.add_middleware(RateLimitMiddleware, default_limit=5, window=60)


async def create_request_and_serve(req: Request, handler):
    try:
        req_data = {**req.path_params, **req.query_params}
        response = handler(req_data).serve()
        if isinstance(response, str):
            return HTMLResponse(content=response, status_code=200)

        return JSONResponse(content=response, status_code=200)
    except Exception as e:
        handle_error(e)

async def create_request_and_serve_jpg(req: Request, handler):
    try:
        req_data = {**req.path_params, **req.query_params}
        file_path_local = handler(req_data).serve()
        return FileResponse(file_path_local, media_type="image/jpeg")
    except Exception as e:
        handle_error(e)

def create_route_handler(handler, is_jpg=False):
    fn = create_request_and_serve_jpg if is_jpg else create_request_and_serve
    return partial(fn, handler=handler)

def add_routes(app, routes):
    for route in routes:
        app.add_api_route(
            route["path"],
            create_route_handler(route["handler"], route.get('is_jpg', False)),
            methods=[route["method"]]
        )

add_routes(app, routes_config)

async def serve_favicon(request):
    return FileResponse('./models/favicon.ico')

app.router.routes.insert(0, Route('/favicon.ico', serve_favicon, include_in_schema=False))

@app.post("/user-rating")
async def save_user_feedback(request: Request):
    data = await request.json()
    with open("user-ratings.tsv", "a") as f:
        f.write(json.dumps(data))
        f.write("\n")
    return JSONResponse(content={"success": True}, status_code=200)

def handle_error(e):
    if isinstance(e, API.ResourceNotFoundError):
        raise HTTPException(status_code=404, detail="Resource not found")
    if isinstance(e, API.BadRequestError):
        raise HTTPException(status_code=400, detail=e.message)
    if isinstance(e, API.ServerError):
        raise HTTPException(status_code=500, detail=e.message)
    if isinstance(e, API.NotAllowedError):
        raise HTTPException(status_code=403, detail=e.message)
    if isinstance(e, HTTPException):
        raise e
    raise HTTPException(status_code=500, detail="Server error")

if os.environ.get("PLUGINS"):
    for plugin in os.environ.get("PLUGINS").split(","):
        try:
            plugin_path = f"plugins.{plugin}.routes"
            module = importlib.import_module(plugin_path)
            if hasattr(module, "route_config"):
                add_routes(app, module.route_config)
                print(f"Loaded plugin {plugin}")
            else:
                print(f"Plugin {plugin} has no routes")
        except Exception as e:
            logging.error(f"Error loading plugin {plugin}: {e}")

if __name__ == "__main__":
    import uvicorn
    PORT = int(os.environ.get("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=PORT, access_log=False)
