import os
import time
import subprocess
import sys
import gzip
import itertools
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

import requests
import numpy as np
import uvicorn
from tqdm.auto import tqdm
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from usearch.index import Index as UsearchIndex
from dotenv import load_dotenv

BASE_DIR = str(Path(__file__).parent.parent.resolve())
sys.path.append(BASE_DIR)

load_dotenv(f"{BASE_DIR}/.env")
indexes_dir = f'{BASE_DIR}/indexes/'

HOST = "127.0.0.1"
PORT = 8002
DEFAULT_ENDPOINT = f'http://{HOST}:{PORT}'
ENDPOINT = os.environ.get('VECTOR_SEARCH_ENDPOINT', DEFAULT_ENDPOINT)
process = None  # To track service status

cache = {
    'indexes': {},
    'labels': {}
}

def load_indexes():
    index_files = []
    for entry in os.scandir(indexes_dir):
        if entry.is_file() and entry.name.endswith('.usearch'):
            index_files.append(entry)

    files = sorted(index_files, key=lambda f: f.name)

    if os.environ.get('ENVIRONMENT') == 'test':
        files = files[-10:]

    for file in tqdm(index_files, desc="Loading indexes", ncols=80, ascii="░▒"):
        load_index(file)

def load_index(file):
    fname = file.path.split('/').pop()
    index_id = fname[:-len('.usearch')]

    view = os.environ.get('LOAD_USEARCH_INDEXES_IN_MEMORY') == '0'
    index = UsearchIndex(ndim=384, metric='cos', path=file.path, view=view)
    cache['indexes'][index_id] = index

    labels_file = file.path[:-len('.usearch')] + '.items.bin.gz'
    with gzip.open(labels_file, 'rb') as f:
        labels = f.read()
    cache['labels'][index_id] = labels


def search_index(t):
    idx, qvec, n = t
    matches = cache['indexes'][idx].search(qvec, n)
    results = [(m.key, idx, 1.0-m.distance) for m in matches]
    return results


def concurrent_search(qvec, n, type=None):
    idxs = cache['indexes'].keys()
    if type in ['patent', 'npl']:
        idxs = [idx for idx in idxs if type in idx]
    args = [(idx, qvec, n) for idx in idxs]

    with ThreadPoolExecutor(max_workers=4) as executor:
        with tqdm(total=len(args), desc="Searching indexes", ncols=80, ascii="░▒") as pbar:
            results = []
            for r in executor.map(search_index, args):
                results.append(r)
                pbar.update(1)

    results = list(itertools.chain.from_iterable(results))
    results = sorted(results, key=lambda x: x[2], reverse=True)

    BYTES_PER_LABEL = 20

    arr = []
    for i, idx, sim in results:
        start = int(i * BYTES_PER_LABEL)
        end = start + BYTES_PER_LABEL
        label = cache['labels'][idx][start:end].decode("utf-8").strip()
        arr.append((label, idx, sim))
    return arr



############################# FASTAPI APP #############################

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_indexes()
    print("Starting vector search service...")
    yield
    print("Shutting down vector search service...")

app = FastAPI(lifespan=lifespan)

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
    cmd = ["uvicorn", "services.vector_search:app", "--port", str(PORT)]
    process = subprocess.Popen(cmd, preexec_fn=os.setpgrp)
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

@app.get('/health')
async def health():
    return {"status": "ok"}


@app.post("/search")
async def search(request: Request):
    payload = await request.json()
    vector = np.array(payload["vector"], dtype=np.float32)
    n = payload.get("n_results", 10)
    type = payload.get("type", 'patent')
    results = concurrent_search(vector, n, type)
    return JSONResponse(content=results)

if __name__ == "__main__":
    uvicorn.run(
        "services.vector_search:app",
        host='0.0.0.0',
        port=PORT,
        access_log=False
    )
