import os
import time
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

import requests
import numpy as np
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

BASE_DIR = str(Path(__file__).parent.parent.resolve())
sys.path.append(BASE_DIR)

from config.config import indexes_dir
from core.indexes import IndexesDirectory

indexdir = IndexesDirectory(indexes_dir)

HOST = "http://127.0.0.1"
PORT = 8002
ENDPOINT = f"http://127.0.0.1:{PORT}"
process = None  # To track service status

cache = {}

def load_indexes():
    for index_id in indexdir.available():
        index = indexdir.get(index_id)[0]
        cache[index_id] = index

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_indexes()
    yield
    print("Shutting down the vector search service.")


app = FastAPI(lifespan=lifespan)

@app.get('/health')
async def health():
    return {"status": "ok"}

def search_index(t):
    idx, qvec, n = t 
    results = cache[idx].search(qvec, n)
    results = [(doc_id, idx, score) for doc_id, score in results]
    return results

def concurrent_search(idxs, qvec, n):
    args = [(idx, qvec, n) for idx in idxs]
    with ProcessPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(search_index, args))
    results = sum(results, [])
    results = sorted(results, key=lambda x: x[2], reverse=True)
    return results

def deduplicate(results):
    if not results:
        return results

    epsilon = 0.000001
    output, rest = results[:1], results[1:]
    added = set()
    for r in rest:
        _id, _, score = r
        if output[-1][-1] - score < epsilon:
            continue
        if _id in added:
            continue
        output.append(r)
        added.add(_id)
    return output

@app.post("/search")
async def search(request: Request):
    if not cache:
        load_indexes()
    payload = await request.json()
    vector = np.array(payload["vector"], dtype=np.float32)
    n = payload.get("n_results", 10)
    indexes = payload.get("indexes")
    indexes = indexdir.available() if indexes == "all" else indexes
    results = concurrent_search(indexes, vector, n)
    results = deduplicate(results)[:n]
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
