import os
import traceback
import json
import importlib
import logging
from functools import partial

from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk
import auth
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from config import config
import core.api as API
import services.vector_search as vector_search

logging.getLogger("uvicorn").setLevel(logging.INFO)

if config.gpu_disabled:
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

SENTRY_URL = os.environ.get("SENTRY_URL").strip()
if SENTRY_URL:
    print("Sentry is active. Errors and performance data will be reported.")
    sentry_sdk.init(
        environment=config.environment, dsn=SENTRY_URL, traces_sample_rate=1.0
    )

app = FastAPI(openapi_url=None, docs_url=None)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if SENTRY_URL:
    app.add_middleware(SentryAsgiMiddleware)

route_config = [
    {"method": "GET", "path": "/search/102/", "handler": API.SearchRequest102},
    {"method": "GET", "path": "/search/103/", "handler": API.SearchRequest103},
    {"method": "GET", "path": "/search/102+103/", "handler": API.SearchRequestCombined102and103},
    {"method": "GET", "path": "/prior-art/patent/", "handler": API.PatentPriorArtRequest},
    {"method": "GET", "path": "/similar/", "handler": API.SimilarPatentsRequest},
    {"method": "GET", "path": "/snippets/", "handler": API.SnippetRequest},
    {"method": "GET", "path": "/mappings/", "handler": API.MappingRequest},
    {"method": "GET", "path": "/datasets/", "handler": API.DatasetSampleRequest},
    {"method": "GET", "path": "/extension/", "handler": API.IncomingExtensionRequest},
    {'method': 'GET', 'path': '/documents/', 'handler': API.DocumentRequest},
    {'method': 'GET', 'path': '/patents/{pn}', 'handler': API.PatentDataRequest},
    {'method': 'GET', 'path': '/patents/{pn}/title', 'handler': API.TitleRequest},
    {'method': 'GET', 'path': '/patents/{pn}/abstract', 'handler': API.AbstractRequest},
    {'method': 'GET', 'path': '/patents/{pn}/claims/', 'handler': API.AllClaimsRequest},
    {'method': 'GET', 'path': '/patents/{pn}/claims/independent', 'handler': API.IndependentClaimsRequest},
    {'method': 'GET', 'path': '/patents/{pn}/claims/{n}', 'handler': API.OneClaimRequest},
    {'method': 'GET', 'path': '/patents/{pn}/description', 'handler': API.PatentDescriptionRequest},
    {'method': 'GET', 'path': '/patents/{pn}/citations', 'handler': API.CitationsRequest},
    {'method': 'GET', 'path': '/patents/{pn}/citations/backward', 'handler': API.BackwardCitationsRequest},
    {'method': 'GET', 'path': '/patents/{pn}/citations/forward', 'handler': API.ForwardCitationsRequest},
    {'method': 'GET', 'path': '/patents/{pn}/citations/aggregated', 'handler': API.AggregatedCitationsRequest},
    {'method': 'GET', 'path': '/patents/{pn}/abstract/concepts', 'handler': API.AbstractConceptsRequest},
    {'method': 'GET', 'path': '/patents/{pn}/description/concepts', 'handler': API.DescriptionConceptsRequest},
    {'method': 'GET', 'path': '/patents/{pn}/classification/cpcs', 'handler': API.CPCsRequest},
    {'method': 'GET', 'path': '/patents/{pn}/vectors/cpcs', 'handler': API.PatentCPCVectorRequest},
    {'method': 'GET', 'path': '/patents/{pn}/vectors/abstract', 'handler': API.PatentAbstractVectorRequest},
    {'method': 'GET', 'path': '/patents/{pn}/thumbnails', 'handler': API.ListThumbnailsRequest},
    {'method': 'GET', 'path': '/patents/{pn}/drawings/', 'handler': API.ListDrawingsRequest},
    {'method': 'GET', 'path': '/patents/{pn}/thumbnails/{n}', 'handler': API.ThumbnailRequest, 'is_jpg': True},
    {'method': 'GET', 'path': '/patents/{pn}/drawings/{n}/', 'handler': API.DrawingRequest, 'is_jpg': True},
    {'method': 'GET', 'path': '/concepts/{concept}/similar', 'handler': API.SimilarConceptsRequest},
    {'method': 'GET', 'path': '/concepts/{concept}/vector', 'handler': API.ConceptVectorRequest},
    {'method': 'GET', 'path': '/docs', 'handler': API.DocumentationRequest}
]

async def create_request_and_serve(req: Request, handler):
    try:
        req_data = {**req.path_params, **req.query_params}
        response = handler(req_data).serve()
        if isinstance(response, str):
            return HTMLResponse(content=response, status_code=status.HTTP_200_OK)

        return JSONResponse(content=response, status_code=status.HTTP_200_OK)
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
    serve_function = create_request_and_serve_jpg if is_jpg else create_request_and_serve
    return partial(serve_function, handler=handler)

async def validate_token(request: Request):
    if not config.token_authentication_active:
        return
    if auth.validate_access(request):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token.")

def add_routes(app, routes):
    for route in routes:
        app.add_api_route(
            route["path"],
            create_route_handler(route["handler"], route.get('is_jpg', False)),
            methods=[route["method"]],
            dependencies=[Depends(validate_token)]
        )

add_routes(app, route_config)

@app.post("/user-rating")
async def save_user_feedback(request: Request):
    data = await request.json()
    with open("user-ratings.tsv", "a") as f:
        f.write(json.dumps(data))
        f.write("\n")
    return JSONResponse(content={"success": True}, status_code=status.HTTP_200_OK)

def handle_error(e):
    if isinstance(e, API.ResourceNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    if isinstance(e, API.BadRequestError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    if isinstance(e, API.ServerError):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.message)
    if isinstance(e, API.NotAllowedError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    traceback.print_exc(e)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error")

if os.environ.get("PLUGINS"):
    for plugin in os.environ.get("PLUGINS").split(","):
        try:
            plugin_path = f"plugins.{plugin}.routes"
            importlib.import_module(plugin_path)
            print(f"Loaded plugin {plugin}")
        except Exception as e:
            logging.error(f"Error loading plugin {plugin}: {e}")

if __name__ == "__main__":
    import uvicorn
    PORT = int(os.environ.get("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=PORT)
