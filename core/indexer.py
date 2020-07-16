import annoy
import faiss
import numpy as np
from psutil import virtual_memory
from math import ceil
from os import path

from config.config import INDEX_DIR


class Indexer():

    class __impl:

        def __init__(self):
            """Summary
            """
            self.dir = INDEX_DIR
            self._cache_enabled = True
            self._cache = {}

        def __getitem__(self, index_id, indexType='faiss'):

            if self._in_cache(index_id, indexType):
                return self._get_index_from_cache(index_id, indexType)
            else:
                index = self._get_index_from_disk(index_id, indexType)
                return index

        def _in_cache(self, index_id, indexType):
            cached = self._cache.get([(index_id, indexType)])
            return bool(cached)

        def _get_index_from_cache(self, index_id, indexType):
            cached = self._cache.get([(index_id, indexType)])
            return cached

        def _add_index_to_cache(self, index_id, indexType, index):
            self._cached[(index_id, indexType)] = index
            return True

        def _get_index_from_disk(self, index_id, indexType):
            if indexType == 'faiss':
                index = IndexFaiss(index_id, self.dir)
            elif indexType == 'annoy':
                index = IndexAnnoy(index_id, self.dir)
            else:
                raise Exception('Invalid index type.')

            if self._cache_enabled:
                self._add_to_cache(index_id, indexType, index)

            return index

    __instance = __impl(distilbert_model_path)

    def __getattr__(self, attr):
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        return setattr(self.__instance, attr, value)

    def __getitem__(self, key):
        return self.__instance.__getitem__(key)


class IndexFaiss():

    def __init__(self, index_id, folder):
        self.index_id = index_id
        self.folder = folder

    def __getitem__(self, index_id):
        pass

    def create(self, index_id, vectors, labels=None):
        ndims = vectors[0].shape[0]
        nclusters = 20
        faiss.normalize_L2(vectors)
        quantiser = faiss.IndexFlatIP(ndims)
        index = faiss.IndexIVFFlat(
            quantiser, ndims, nclusters, faiss.METRIC_INNER_PRODUCT)
        index.train(vectors)
        faiss.write_index(index_id, f"{self.folder}Original.{index_id}.index")

    def distribution(self, vectors):
        ndims = vectors[0].shape[0]
        nvecs = vectors.shape[0]
        mem = virtual_memory()
        prev_div_factor = 0
        if(path.isfile(f"{self.folder}div_factor.txt")):
            file = open(f"{self.folder}div_factor.txt", "w+")
            prev_div_factor = int(file.readline([0]))
        else:
            file = open(f"{self.folder}div_factor.txt", "w")
        
        div_factor = ceil(nvecs*ndims*4/mem.total) # 4: Size of one block of vector(in bytes)
        file.write(f"{prev_div_factor+div_factor}")
        file.close()
        for i in range(prev_div_factor, prev_div_factor+div_factor):
            index = faiss.read_index(
                f"{self.folder}{self.index_id}.Original.index")
            llim = int(i*(nvecs/div_factor))
            ulim = int((i+1)*(nvecs/div_factor))
            ids = np.arange(llim, ulim)
            index.add_with_ids(vectors[llim:ulim], ids)
            faiss.write_index(
                index, f"{self.folder}{self.index_id}.index{i+1}.index")
        ivf = []
        for i in range(div_factor):
            index = faiss.read_index(
                f"{self.folder}{self.index_id}.index{i+1}.index", faiss.IO_FLAG_MMAP)
            ivf.append(index.invlists)
            index.own_invlists = False # to stop deallocation.
        return ivf

    def add_vectors(self, vectors, labels=None):
        nvecs = vectors.shape[0]

        # Distributing index into smaller parts
        ivf = distribution(vectors)
        # Merging on the disk
        index = faiss.read_index(
            f"{self.folder}{self.index_id}.Original.index")
        invlists = faiss.OnDiskInvertedLists(
            nclusters, index.code_size, f"{self.folder}{self.index_id}.merged_index.ivfdata")
        ivf_vector = faiss.InvertedListsPtrVector()
        for i in ivf:
            ivf_vector.push_back(i)
        ntotal = invlists.merge_from(ivf_vector.data(), ivf_vector.size())
        index.ntotal = ntotal
        index.replace_invlists(invlists)
        faiss.write_index(index, f"{self.folder}{self.index_id}.index")
        return True

    def get_vectors(self):
        pass

    def get_labels(self, idxs=None):
        with open(f"{self.folder}G06N.ann.items.json") as f:
            data = json.load(f)
        labels = np.array(data)
        return labels

    def find_similar(self, query_vectors, n):
        index = faiss.read_index(
            f"{self.folder}{self.index_id}.index", faiss.IO_FLAG_MMAP)
        nearest_neighbours = n
        indices = index.search(query_vectors, nearest_neighbours)[1]
        return indices

    def find_similar_with_dist(self, query_vectors, n):
        index = faiss.read_index(
            f"{self.folder}{self.index_id}.index", faiss.IO_FLAG_MMAP)
        nearest_neighbours = n
        distances = index.search(query_vectors, nearest_neighbours)[0]
        return distances

    def get_n_items():
        pass


class IndexAnnoy():

    def __init__(self, index_id, folder):
        self.index_id = index_id
        self.folder = folder
        self.index_file_path = f"{self.folder}{self.index_id}.ann"
        self.labels_file_path = f"{self.index_file_path}.items.json"
        self.dims = None

    def __getitem__(self, index_id):
        pass

    def create(self, vectors, labels=None):
        nvecs = vectors.shape[0]
        self.ndims = vectors.shape[1]
        index = annoy.AnnoyIndex(self.ndims, 'angular')
        for i in range(nvecs):
            index.add_item(i, vectors[i])
        ntrees = 20
        index.build(ntrees)
        index.save(self.index_file_path)
        if labels is None:
        	labels = list(range(nvecs))
        with open(self.labels_file_path) as f:
        	f.write(json.dumps(labels))
        return True

    def get_vectors(self):
        index = annoy.AnnoyIndex(self.ndims, 'angular')
        index.load(self.index_file_path)
        vecs = np.empty((index.get_n_items(), self.ndims), 'float32')
        for j in range(nvecs):
            vecs[j] = index.get_item_vector(j)
        return vecs

    def get_labels(self, idxs=None):
        with open(f"{self.folder}G06N.ann.items.json") as f:
            data = json.load(f)
        labels = np.array(data)
        return labels

    def find_similar(self, query_vectors, n):
        index.load(f"{self.index_id}.ann")
        nearest_neighbours = n
        indices = index.get_nns_by_vector(
            query_vectors, nearest_neighbours, include_distances=False)
        return indices

    def find_similar_with_dist(self, query_vectors, n):
        index.load(f"{self.index_id}.ann")
        nearest_neighbours = n
        distances = index.get_nns_by_vector(
            query_vectors, nearest_neighbours, include_distances=True)[1]
        return distances

    def get_n_items():
        return index.get_n_items()