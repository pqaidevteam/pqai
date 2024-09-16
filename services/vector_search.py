import os
import time
import subprocess

import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import numpy as np
from contextlib import asynccontextmanager

from config.config import indexes_dir
from core.indexes import IndexesDirectory
from core.search import VectorIndexSearcher

available_indexes = IndexesDirectory(indexes_dir)
vector_search = VectorIndexSearcher().search

HOST = "http://127.0.0.1"
PORT = 8002
ENDPOINT = f"http://127.0.0.1:{PORT}"
process = None  # To track service status


@asynccontextmanager
async def lifespan(app: FastAPI):
    available_indexes.get("all")  # Load indexes in memory

    yield

    print("Shutting down the vector search service.")


app = FastAPI(lifespan=lifespan)

@app.get('/health')
async def health():
    return {"status": "ok"}

@app.post("/search")
async def search(request: Request):
    payload = await request.json()
    vector = np.array(payload["vector"], dtype=np.float32)
    n = payload.get("n_results", 10)
    indexes = []
    for idx_id in payload.get("indexes", []):
        indexes += available_indexes.get(idx_id)
    results = vector_search(vector, indexes, n)
    return JSONResponse(content=results)


def ready() -> bool:
    try:
        response = requests.get(f"{ENDPOINT}/health", timeout=2)
        return response.status_code == 200
    except requests.ConnectionError:
        return False


def start():
    global process
    if ready():
        print("Vector search service is already operational.")
        return

    print("Starting vector search service...")
    process = subprocess.Popen(
        ["uvicorn", "services.vector_search:app", "--port", str(PORT)],
        preexec_fn=os.setpgrp,
    )
    time.sleep(2)


def stop():
    global process
    if process is not None:
        process.terminate()
        process.wait()
        print("Vector search service stopped.")


def send(request_payload: dict):
    response = requests.post(f"{ENDPOINT}/search", json=request_payload)
    results = response.json()
    return results


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.vector_search:app",
                host="127.0.0.1",
                port=PORT,
                access_log=False)
