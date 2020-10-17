import numpy as np
import annoy
import json
import os

from config.config import indexes_dir

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

    def read_from_ann_json(self, ann_file, json_file, name=None):
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

    def __init__(self, directory, idx_name):
        pass


class FaissIndex(VectorIndex):

    def __init__(self):
        pass


class IndexesDirectory():

    cache = {}
    dims = 768
    metric = 'angular'

    def __init__(self, folder):
        self._folder = folder
        self._available = self._discover_indexes()

    def _discover_indexes(self):
        files = os.scandir(self._folder)
        ann_files = [f for f in files if f.name.endswith('.ann')]
        index_ids = [f.name[:-4] for f in ann_files]
        return set(index_ids)

    def get(self, index_id):
        index_ids = filter(lambda x: x.startswith(index_id), self.available())
        indexes = [self._get_one_index(idx) for idx in index_ids]
        return indexes

    def _get_one_index(self, index_id):
        if index_id in self.cache:
            return self.cache.get(index_id)
        return self._get_from_disk(index_id)

    def _get_from_disk(self, index_id):
        ann_file = f'{self._folder}/{index_id}.ann'
        json_file = f'{self._folder}/{index_id}.items.json'
        reader = AnnoyIndexReader(self.dims, self.metric)
        index = reader.read_from_ann_json(ann_file, json_file, name=index_id)
        self._cache_index(index_id, index)
        return index

    def _cache_index(self, index_id, index):
        self.cache[index_id] = index

    def available(self):
        return self._available
