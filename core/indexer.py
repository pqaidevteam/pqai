import annoy
import faiss
import numpy as np
from psutil import virtual_memory
from math import ceil
from os import path
import json

#from config.config import INDEX_DIR


class Indexer():

    """
    Loads and caches vector indexes of various types (Annoy, FAISS).
    """
    
    class __impl:

        """
        A singleton class to make sure that only one copy of this
        class exists in the memory. This is important because its
        instances caches data in memory and multiple copies may lead to
        caching of redundant data leading to increased memory
        consumption.
        """
        def __init__(self):
            """Initialize an Indexer class.
            """

            # directory where indexes are stored
            self._dir = INDEX_DIR

            # enabling this will speed up the search but will consume
            # more momory
            self._cache_enabled = True

            self._cache = {}
            self._default_index_type = 'faiss'

        def __getitem__(self, index_id):
            """Get an index with given name.
            
            Args:
                index_id (str): The index's name.
            
            Returns:
                Index: The Index object corresponding to the requested
                    `index_id`.
                    """
            return self.get_index(index_id)
                    
        def get_index(self, index_id, index_type=None):
            """Get the index with the given name and type.
            
            Args:
                index_id (str): The index's name.
                index_type (str, optional): The index's type, e.g.,
                    'annoy' or 'faiss'.
            
            Returns:
                Index: The Index object corresponding to the given
                    name and index type.
                    """
            index_type = self._default_index_type
            if self._in_cache(index_id, index_type):
                return self._get_index_from_cache(index_id, index_type)
            else:
                index = self._get_index_from_disk(index_id, index_type)
            return index

        def _in_cache(self, index_id, index_type):
            """Check whether an index is cached in the memory.
            
            Args:
                index_id (str): The index's name.
                index_type (str): The index's type.
            
            Returns:
                bool: True if the index is available in the cache, False
                    otherwise.
                    """
            key = (index_id, index_type)
            return key in self._cache

        def _get_index_from_cache(self, index_id, index_type):
            """Return the specified Index object from the cache.

            Args:
                index_id (str): The index's name.
                index_type (str): The index's type.
            
            Returns:
                Index: The Index object corresponding to the given
                    name and index type.
                    """
            key = (index_id, index_type)
            cached = self._cache.get(key)
            return cached

        def _add_index_to_cache(self, index_id, index_type, index):
            """Add the index to in-memory cache.
            
            Args:
                index_id (str): The Index's name.
                index_type (str): The Index's type.
                index (Index): An object of the class Index.
            
            Returns:
                bool: True if caching successful, False otherwise.
                """
            key = (index_id, index_type)
            self._cache[key] = index
            return key in self._cache

        def _get_index_from_disk(self, index_id, index_type):
            """Return the specified Index object by loading it from the
                disk.

            Args:
                index_id (str): The index's name.
                index_type (str): The index's type.
            
            Returns:
                Index: The Index object corresponding to the given
                    name and index type.
                    """
            if index_type == 'faiss':
                index = IndexFaiss(index_id, self._dir)
            elif index_type == 'annoy':
                index = IndexAnnoy(index_id, self._dir)
            else:
                raise Exception('Invalid index type.')

            # Cache for later use
            if self._cache_enabled:
                self._add_to_cache(index_id, index_type, index)

                return index

    #__instance = __impl(distilbert_model_path)

        def __getattr__(self, attr):
            return getattr(self.__instance, attr)

        def __setattr__(self, attr, value):
            return setattr(self.__instance, attr, value)

            def __getitem__(self, key):
                return self.__instance.__getitem__(key)

class IndexAnnoy():

    def __init__(self, index_id, folder):
        self.index_id = index_id
        self.folder = folder
        self.index_file_path = f"{self.folder}/{self.index_id}.ann"
        self.labels_file_path = f"{self.index_file_path}.items.json"
        self.dims = None
        self.ndims = 256

    def __getitem__(self, index_id):
        pass

    def create(self, vectors, labels=None):
        """Create Annoy index file for user.

        Args:
            vectors(nd array): vectors to create index.
            labels (list): labels list if already exists.

        Returns:
            True if Annoy index is created.
        """
        self.nvecs = vectors.shape[0]
        index = self._build_index(vectors)
        labels = self._create_labels(labels)
        return True

    def _build_index(self, vectors):
        """Build Annoy index with the given vectors.

        Args: 
            vectors(nd array): vectors to create index.

        Returns:
            index: The index created and saved.
        """
        index = annoy.AnnoyIndex(self.ndims, 'angular')
        for i in range(self.nvecs):
            index.add_item(i, vectors[i])
        ntrees = 20
        index.build(ntrees)
        index.save(self.index_file_path)
        return index

    def _create_labels(self, labels):
        """Creates labels for the index.

        Args:
            labels (list): labels list if already exists.

        Returns:
            labels (list): New created labels list.
        """
        if labels is None:
            labels = list(range(self.nvecs))
        with open(self.labels_file_path, 'w+') as f:
            f.write(json.dumps(labels))
        return labels

    def get_vectors(self):
        """Exract vectors from Annoy index file.

        Returns:
            vectors(nd array): All vectors in index file. 
        """
        index = annoy.AnnoyIndex(self.ndims, 'angular')
        index.load(self.index_file_path)
        vectors = np.empty((index.get_n_items(), self.ndims), 'float32')
        for j in range(index.get_n_items()):
            vectors[j] = index.get_item_vector(j)
        return vectors

    def get_labels(self):
        """Exract labels from Annoy index file.

        Returns:
            vectors(nd array): All labels in index file. 
        """
        with open(self.labels_file_path) as f:
            data = json.load(f)
        labels = np.array(data)
        return labels

    def find_similar(self, query_vectors, n):
        """Search n nearest neighbours from the index file.

        Args:
            query_vectors(nd array): vectors to be searched.
            n (int): number of nearest neighbours.

        Returns:
            indices (nd array): indices of search result vectors.  
        """
        index = annoy.AnnoyIndex(self.ndims, 'angular')
        index.load(self.index_file_path)
        nearest_neighbours = n
        indices = index.get_nns_by_vector(
            query_vectors, nearest_neighbours, include_distances=False)
        return indices

    def find_similar_with_dist(self, query_vectors, n):
        """Provide distance of n nearest neighbours from query vector.

        Args:
            query_vectors(nd array): vectors to be searched.
            n (int): number of nearest neighbours.

        Returns:
            distances (nd array): distances of each search result from query vectors. 
        """
        index = annoy.AnnoyIndex(self.ndims, 'angular')
        index.load(self.index_file_path)
        nearest_neighbours = n
        distances = index.get_nns_by_vector(
            query_vectors, nearest_neighbours, include_distances=True)[1]
        return distances

    def get_n_items(self):
        """Returns the number of items in the index.
        """
        index = annoy.AnnoyIndex(self.ndims, 'angular')
        index.load(self.index_file_path)
        return index.get_n_items()

class IndexFaiss():

    def __init__(self, index_id, folder):
        """Initialize
        
        Args:
            index_id (str): Name of index
            folder (str): Filesystem path where index is (or will be)
            stored
        """
        self._n_clusters = 20
        self._index_id = index_id
        self._folder = folder[:-1] if folder.endswith('/') else folder
        self._index_file = f'{self._folder}/{self._index_id}.index'
        self._labels_file = f'{self._folder}/{self._index_id}.labels.json'
        self._div_factor_file = f'{self._folder}/{self._index_id}.divf.txt'
        self._metric = faiss.METRIC_INNER_PRODUCT
        self._labels = None
        self._index = None

    def __getitem__(self, item_label):
        pass

    def create(self, vectors, labels=None):
        """Create a new index with the given id and vectors.
        
        Args:
            vectors (nd array): vectors to create index
            labels (None, optional): Labels for the vectors
        """
        self._n_dims = vectors[0].shape[0]
        if len(labels)!=0:
            self._labels = list(range(len(vectors)))

        self._build_index(vectors)
        self._write_labels_file()
        self._write_index_file()

    def _build_index(self, vectors):
        """Build index structure.

        Args:
            vectors (nd array): vectors to create index
        """
        faiss.normalize_L2(vectors)
        quantiser = faiss.IndexFlatIP(self._n_dims)
        self._index = faiss.IndexIVFFlat(
            quantiser, self._n_dims, self._n_clusters, self._metric)
        self._index.train(vectors)

    def _write_index_file(self):
        """Write index to disk.
        """
        faiss.write_index(self._index, f'{self._folder}/{self._index_id}.Original.index')

    def _write_labels_file(self):
        """Write labels to disk.
        """
        with open(self._labels_file, 'w') as file:
            file.write(json.dumps(self._labels))

    def add_vectors(self, vectors, labels=None):
        """Add vectors to existing index.

        Args: 
            vectors (nd array): vectors to create index
            labels (None, optional): Labels for the vectors

        Returns:
            True if vectors are added
        """
        self._n_vecs = len(vectors)
        self._n_dims = vectors[0].shape[0]
        ivf = self._distribute_vectors(vectors)
        self._merge_index(ivf)
        return True

    def _distribute_vectors(self, vectors):
        """Distribute vectors into smaller parts

        Args:
            vectors (nd array): vectors to create index

        Returns:
            ivf (object): Inverted index
        """
        prev_div_factor = self._calculate_prev_div_factor()
        div_factor = self._calculate_div_factor(prev_div_factor)
        self._create_branch_index(div_factor, vectors)
        return self._create_ivf()

    def _calculate_prev_div_factor(self):
        """Extract previous division factor.

        Returns:
            prev_div_factor (int): previous division factor
        """
        prev_div_factor = 0
        if (path.isfile(self._div_factor_file)):
            with open(self._div_factor_file, 'r') as file:
                prev_div_factor = int(file.read().strip().splitlines()[0])
        return prev_div_factor

    def _calculate_div_factor(self, prev_div_factor):
        """Extract current division factor.

        Returns:
            div_factor (int): current division factor
        """
        mem = virtual_memory()
        div_factor = ceil(self._n_vecs*self._n_dims*4/mem.total)
        self._div_factor = prev_div_factor + div_factor
        with open(self._div_factor_file, 'w+') as file:
            file.write(f'{self._div_factor}')
        return div_factor      

    def _create_branch_index(self, div_factor, vectors):
        """Creating indices of smaller size.

        Args:
            div_factor (int): current division factor
        """
        for i in range(div_factor):
            index = faiss.read_index(f'{self._folder}/{self._index_id}.Original.index')
            llim = int(i*(self._n_vecs/div_factor))
            ulim = int((i+1)*(self._n_vecs/div_factor))
            ids = np.arange(llim, ulim)
            index.add_with_ids(vectors[llim:ulim], ids)
            faiss.write_index(index, f'{self._folder}/{self._index_id}{self._div_factor-div_factor+i+1}.index')

    def _create_ivf(self):
        """Creating inverted list for all smaller indices.

        Return:
            ivf (list): inverted list
        """
        ivf = []
        for i in range(self._div_factor):
            index = faiss.read_index(f'{self._folder}/{self._index_id}{i+1}.index', faiss.IO_FLAG_MMAP)
            ivf.append(index.invlists)
            index.own_invlists = False # to stop deallocation.
        return ivf

    def _merge_index(self, ivf):
        """Merging all indices created in smaller size.

        Args:
            ivf (list): inverted list
        """
        self._index = faiss.read_index(f'{self._folder}/{self._index_id}.Original.index')
        invlists = faiss.OnDiskInvertedLists(
            self._n_clusters, self._index.code_size, f"{self._folder}/{self._index_id}.merged_index.ivfdata")
        ivf_vector = self._create_ivf_vector(ivf)
        ntotal = invlists.merge_from(ivf_vector.data(), ivf_vector.size())
        self._index.ntotal = ntotal
        self._index.replace_invlists(invlists)
        faiss.write_index(self._index, self._index_file)

    def _create_ivf_vector(self, ivf):
        """Creating inverted list vector.

        Args:
            ivf (list): inverted list

        Returns:
            ivf_vector (vector): inverted list vector
        """
        ivf_vector = faiss.InvertedListsPtrVector()
        for invlists in ivf:
            ivf_vector.push_back(invlists)
        return ivf_vector

    def get_labels(self):
        """Provide labels for vectors in index.

        Returns:
            labels (nd array): labels of vectors
        """
        with open(self._labels_file) as f:
            data = json.load(f)
            labels = np.array(data)
        return labels

    def find_similar(self, query_vectors, n):
        """Searching n nearest neighbours from query vector.

        Args:
            query_vectors(nd array): vectors to be searched.
            n (int): number of nearest neighbours.

        Returns:
            indices (nd array): indices of search result vectors. 
        """
        index = faiss.read_index(self._index_file, faiss.IO_FLAG_MMAP)
        nearest_neighbours = n
        indices = index.search(query_vectors, nearest_neighbours)[1]
        return indices

    def find_similar_with_dist(self, query_vectors, n):
        """Provide distance of n nearest neighbours from query vector.

        Args:
            query_vectors(nd array): vectors to be searched.
            n (int): number of nearest neighbours.

        Returns:
            distances (nd array): distances of each search result from query vectors. 
        """
        index = faiss.read_index(self._index_file, faiss.IO_FLAG_MMAP)
        nearest_neighbours = n
        distances = index.search(query_vectors, nearest_neighbours)[0]
        return distances