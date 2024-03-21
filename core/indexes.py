import numpy as np
import annoy
import json
import os
import faiss
import psutil
import usearch.index

from config import config

CHECK_MARK = u'\u2713'

class Index():

    def __init__(self):
        self._search_fn = None
        self._type = 'Index'

    def search(self, query, n):
        return self._search_fn(query, n)

    @property
    def type(self):
        return self._type
    

class VectorIndex(Index):
    
    def __init__(self):
        self._type = 'VectorIndex'


class AnnoyIndexReader():

    def __init__(self, dims, metric):
        self._dims = dims
        self._metric = metric

    def read_from_files(self, ann_file, json_file, name=None):
        index = self._read_ann(ann_file)
        items = self._get_items_from_json(json_file)
        item_resolver = items.__getitem__
        return AnnoyIndex(index, item_resolver, name)

    def _read_ann(self, ann_file):
        index = annoy.AnnoyIndex(self._dims, self._metric)
        index.load(ann_file)
        return index

    def _get_items_from_json(self, json_file):
        with open(json_file) as file:
            items = json.load(file)
        return items


class AnnoyIndex(VectorIndex):

    def __init__(self, index, resolver_fn, name=None):
        self._index = index
        self._index2item = resolver_fn
        self._name = name
        self._search_depth = 1000

    def _search_fn(self, qvec, n):
        ids, dists = self._get_similar(qvec, n)
        items = [self._index2item(i) for i in ids]
        return list(zip(items, dists))

    def _get_similar(self, qvec, n):
        d = self._search_depth
        return self._index.get_nns_by_vector(qvec, n, d, True)

    def set_search_depth(self, d):
        self._search_depth = d

    def count(self):
        return self._index.get_n_items()

    def dims(self):
        v0 = self._index.get_item_vector(0)
        return len(v0)

    def __repr__(self):
        idx_type = 'AnnoyIndex '
        idx_name = 'Unnamed' if self._name is None else self._name
        idx_info = f' [{self.count()} vectors, {self.dims()} dimensions]'
        separator = ' '
        return separator.join([idx_type, idx_name, idx_info])

    @property
    def name(self):
        return self._name


class FaissIndexReader():

    def read_from_files(self, index_file, json_file, name=None):
        index = faiss.read_index(index_file)
        items = self._get_items_from_json(json_file)
        item_resolver = items.__getitem__
        return FaissIndex(index, item_resolver, name)

    def _get_items_from_json(self, json_file):
        with open(json_file) as fp:
            items = json.load(fp)
        return items


class FaissIndex(VectorIndex):

    def __init__(self, index=None, resolver_fn=None, name=None):
        self._id = name
        self._index = index
        self._index2label = resolver_fn
        self._labels = None
        self._dims = None

    def _search_fn(self, qvec, n):
        Q = self._preprocess([qvec])
        ds, ns = self._index.search(Q, n)
        items = [self._index2label(i) for i in ns[0]]
        dists = [float(d) for d in ds[0]]
        return list(zip(items, dists))

    # TODO: Move this to indexer
    def add_vectors(self, vectors, labels):
        if len(vectors) != len(labels):
            raise ValueError('Vector must map one-to-one with labels.')
        X = self._preprocess(vectors)
        if self._index is None:
            self._init(X)
        self._index.add(X)
        self._labels += labels
        self._save()

    def _init(self, X):
        self._dims = X.shape[1]
        self._labels = []
        self._index = faiss.index_factory(self._dims, "OPQ16_64,HNSW32")
        self._index.train(X)

    def _preprocess(self, vectors):
        X = np.array(vectors).astype('float32')
        faiss.normalize_L2(X)
        return X

    def _save(self):
        index_file = f'{self._index_dir}/{self._id}.faiss'
        labels_file = f'{self._index_dir}/{self._id}.items.json'
        faiss.write_index(self._index, index_file)
        with open(labels_file, 'w') as fp:
            json.dump(self._labels, fp)

    @property
    def name(self):
        return self._id


class IndexesDirectory():

    cache = {}
    dims = 1024
    metric = 'angular'
    use_faiss_indexes = config.use_faiss_indexes
    use_annoy_indexes = config.use_annoy_indexes
    use_usearch_indexes = config.use_usearch_indexes

    def __init__(self, folder):
        self._folder = folder
        self._available = self._discover_indexes()

    def _discover_indexes(self):
        files = [f.name for f in os.scandir(self._folder)]
        index_files = []

        if self.use_faiss_indexes:
            index_files += [f for f in files if f.endswith('.faiss')]
        if self.use_annoy_indexes:
            index_files += [f for f in files if f.endswith('.ann')]
        if self.use_usearch_indexes:
            index_files += [f for f in files if f.endswith('.usearch')]
        
        index_ids = ['.'.join(f.split('.')[:-1]) for f in index_files]
        return set(index_ids)

    def get(self, index_id):
        if index_id == "*" or index_id == "all":
            return [self._get_one_index(idx) for idx in self.available()]
        
        index_ids = filter(lambda x: x.startswith(index_id), self.available())
        indexes = [self._get_one_index(idx) for idx in index_ids]
        return indexes

    def _get_one_index(self, index_id):
        if index_id in self.cache:
            return self.cache.get(index_id)
        return self._get_from_disk(index_id)

    def _get_from_disk(self, index_id):
        print(f'Loading vector index: {index_id}')

        index_file = self._get_index_file_path(index_id)
        json_file = f'{self._folder}/{index_id}.items.json'

        if index_file.endswith('faiss'):
            reader = FaissIndexReader()
        elif index_file.endswith('ann'):
            reader = AnnoyIndexReader(self.dims, "angular")
        elif index_file.endswith('usearch'):
            reader = USearchIndexReader(self.dims, "cos")
        else:
            raise ValueError(f'Unknown index file type: {index_file}')
        
        index = reader.read_from_files(index_file, json_file, name=index_id)
        self._cache_index(index_id, index)
        print(f"  {CHECK_MARK} RAM usage: {psutil.virtual_memory()._asdict().get('percent')}%")
        return index

    def _get_index_file_path(self, index_id):
        faiss_file = f'{self._folder}/{index_id}.faiss'
        if self.use_faiss_indexes and os.path.exists(faiss_file):
            return faiss_file
        
        ann_file = f'{self._folder}/{index_id}.ann'
        if self.use_annoy_indexes and os.path.exists(ann_file):
            return ann_file
        
        usearch_file = f'{self._folder}/{index_id}.usearch'
        if self.use_usearch_indexes and os.path.exists(usearch_file):
            return usearch_file

        raise ValueError(f'Index file not found for {index_id}')

    def _cache_index(self, index_id, index):
        self.cache[index_id] = index

    def available(self):
        return self._available


class USearchIndex(VectorIndex):
    
        def __init__(self, index=None, resolver_fn=None, name=None):
            self._id = name
            self._index = index
            self._index2label = resolver_fn
            self._labels = None
            self._dims = None
    
        def _search_fn(self, qvec, n):
            matches = self._index.search(qvec, n)
            labels = [self._index2label(m.key) for m in matches]
            dists = [float(m.distance) for m in matches]
            return list(zip(labels, dists))
        
        @property
        def name(self):
            return self._id


class USearchIndexReader:

    def __init__(self, dims, metric):
        self._dims = dims
        self._metric = metric

    def read_from_files(self, index_file, json_file, name=None):
        index = usearch.index.Index(ndim=self._dims, metric=self._metric)
        if config.load_usearch_indexes_in_memory:
            index.load(index_file)
        else:
            index.view(index_file)
        items = self._get_items_from_json(json_file)
        item_resolver = items.__getitem__
        return USearchIndex(index, item_resolver, name)

    def _get_items_from_json(self, json_file):
        with open(json_file) as fp:
            items = json.load(fp)
        return items