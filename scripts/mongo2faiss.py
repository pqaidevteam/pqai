"""
Create indexes for documents pulled from a Mongo DB collection

This script can be modified for creating indexes of documents from any source
Supports FAISS, USearch, and Annoy index types
"""

import sys
import argparse
import gzip
import json
from pathlib import Path
import numpy as np
from tqdm import tqdm
from pymongo import MongoClient
import annoy
import faiss
import usearch.index

MONGO_URI = 'mongodb://localhost:27017'
MONGO_DB = 'pqai'
MONGO_COLL = 'patent'
THIS_DIR = str(Path(__file__).parent.resolve())
BASE_DIR = str(Path(__file__).parent.parent.resolve())
INDEXES_DIR = "{}/indexes".format(BASE_DIR)

INDEX_NAME = "test"

sys.path.append(BASE_DIR)
from core.indexes import FaissIndex, AnnoyIndex, USearchIndex
from core.vectorizers import SentBERTVectorizer

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Create indexes for documents from MongoDB collection'
    )
    parser.add_argument(
        'year',
        type=int,
        help='Year to filter documents (e.g., 2021)'
    )
    parser.add_argument(
        'index_type',
        type=str,
        choices=['faiss', 'usearch', 'annoy'],
        help='Type of index to create: faiss, usearch, or annoy'
    )
    return parser.parse_args()

def create_faiss_index(vectors, labels, index_name, index_dir):
    """Create and save a FAISS index"""
    index = FaissIndex(name=index_name)
    index._index_dir = index_dir
    index.add_vectors(vectors, labels)
    print(f'FAISS index saved in {index_dir}')

def create_annoy_index(vectors, labels, index_name, index_dir):
    """Create and save an Annoy index"""
    n_dims = vectors.shape[1]
    n_trees = 20
    
    index = annoy.AnnoyIndex(n_dims, 'angular')
    for i in range(len(vectors)):
        index.add_item(i, vectors[i])
    
    index.build(n_trees)
    
    index_file = f'{index_dir}/{index_name}.ann'
    labels_file = f'{index_dir}/{index_name}.items.json'
    
    index.save(index_file)
    with open(labels_file, 'w') as f:
        json.dump(labels, f)
    
    print(f'Annoy index saved in {index_dir}')

def create_usearch_index(vectors, labels, index_name, index_dir):
    """Create and save a USearch index"""
    n_dims = vectors.shape[1]
    
    # Normalize vectors for cosine similarity
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors_normalized = vectors / norms
    
    # Create USearch index
    index = usearch.index.Index(ndim=n_dims, metric='cos')
    
    # Add vectors
    keys = np.arange(len(vectors))
    index.add(keys, vectors_normalized)
    
    # Save index
    index_file = f'{index_dir}/{index_name}.usearch'
    index.save(index_file)
    
    # Save labels in binary format (20 bytes per label, matching the reader)
    BYTES_PER_LABEL = 20
    labels_file = f'{index_dir}/{index_name}.items.bin.gz'
    
    labels_bytes = bytearray()
    for label in labels:
        label_str = str(label)[:BYTES_PER_LABEL].ljust(BYTES_PER_LABEL)
        labels_bytes.extend(label_str.encode('utf-8'))
    
    with gzip.open(labels_file, 'wb') as f:
        f.write(labels_bytes)
    
    print(f'USearch index saved in {index_dir}')

if __name__ == '__main__':
    args = parse_arguments()
    
    vectorizer = SentBERTVectorizer()
    N_DIMS = vectorizer.embed('sample string').shape[0]

    client = MongoClient(MONGO_URI)
    collection = client[MONGO_DB][MONGO_COLL]
    # Query for documents from the specified year
    query = {'publicationDate': {'$gte': f'{args.year}-01-01', '$lt': f'{args.year + 1}-01-01'}}

    N = collection.count_documents(query)
    if N == 0:
        print(f'No documents found for year {args.year}')
        sys.exit(0)
    
    N = 5345
    
    print(f'Found {N} documents for year {args.year}')
    
    # Process documents in batches directly from MongoDB cursor
    BATCH_SIZE = 128  # Adjust based on available memory
    cursor = collection.find(query).limit(N)
    
    labels = []
    vectors = []
    
    print('Processing documents in batches...')
    batch_labels = []
    batch_texts = []
    
    for doc in tqdm(cursor, total=N, desc='Vectorizing'):
        pn = doc['publicationNumber']
        text = doc.get('abstract', '')
        
        batch_labels.append(pn)
        batch_texts.append(text)
        
        # When batch is full, vectorize it
        if len(batch_texts) >= BATCH_SIZE:
            batch_vectors = vectorizer.encode_many(batch_texts)
            vectors.append(batch_vectors)
            labels.extend(batch_labels)
            
            # Reset batch
            batch_labels = []
            batch_texts = []
    
    # Process remaining documents in the last incomplete batch
    if batch_texts:
        batch_vectors = vectorizer.encode_many(batch_texts)
        vectors.append(batch_vectors)
        labels.extend(batch_labels)
    
    # Combine all batches
    vectors = np.vstack(vectors)

    print('Indexing...')
    index_name = f"{INDEX_NAME}_{args.year}_{args.index_type}"
    
    # Create the appropriate index type
    if args.index_type == 'faiss':
        create_faiss_index(vectors, labels, index_name, INDEXES_DIR)
    elif args.index_type == 'annoy':
        create_annoy_index(vectors, labels, index_name, INDEXES_DIR)
    elif args.index_type == 'usearch':
        create_usearch_index(vectors, labels, index_name, INDEXES_DIR)
    else:
        raise ValueError(f"Unsupported index type: {args.index_type}")
