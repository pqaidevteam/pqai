import numpy as np
from annoy import AnnoyIndex
import json
from os.path import isfile

from config.config import indexes_dir

index_ids = ['H04W', 'G06T', 'G06N', 'Y02E']
loaded_indexes = {}

def get_index(index_id):
    """Load the .ann and .items.json file for the index.

    Employs lazy loading. Indexes are loaded when they are required to
    be searched by the index. Loading occurs only once; thereafter, the
    same loaded instance is used for searching.
    
    Args:
        index_id (str): Index identifier; the name with which the .ann
            file is saved.
    """
    if type(index_id) is not str:
        return None

    if index_id in loaded_indexes:
        return loaded_indexes[index_id]

    index_file = f"{indexes_dir}{index_id}.ann"
    items_file = f"{indexes_dir}{index_id}.ann.items.json"
    if not (isfile(index_file) or isfile(items_file)):
        return None

    index = Index(index_file, items_file)
    loaded_indexes[index_id] = index
    return index


class Index():

    """An annoy index along with identifiers for its items.
    
    Attributes:
        index_id (str): Index's name, e.g., 'H04W'
        items_list (list): List of item "names", e.g., patent numbers
        vector_index (annoy.AnnoyIndex): The annoy index object, for
            details, check https://github.com/spotify/annoy
    """
    
    def __init__(self, ann_file, json_file):
        """Load an index's data into the memory if not already loaded
            and return a pointer to it.
        
        Args:
            index_id (str): Index's name, e.g., 'H04W'
        """
        self.index = AnnoyIndex(256, metric='angular')
        self.index.load(ann_file)
        self.n_items = self.index.get_n_items()
        self.items = json.load(open(json_file, 'r'))

    def __getitem__(self, value):
        """Return vector for the i-th item.
        
        Args:
            i (int or str): Item number if `int`, item name if `str`.
        
        Returns:
            numpy.ndarray: Item vector
        """
        i = value if type(i) is int else self.items.index(value)
        if -1 < i < self.n_items:
            return self.index.get_item_vector(i)
        else:
            return None

    def find_similar_to_vector (self, query_vec, n=10, dist=False):
        """Summary
        
        Args:
            query_vec (numpy.ndarray): Query vector, must have same
                dimensions as all other vectors in the index.
            n (int, optional): Number of items to return.
            dist (bool, optional): If True, items are returned as pairs
                of item ids (integer) and distances; if False, only
                item ids are returned.
        
        Returns:
            list: Similar items as a list of item ids (if dist=False),
                or tuples (item_id, distance) if dist=True.
        """
        ids, dists = self.index.get_nns_by_vector(query_vec, n, -1, True)
        doc_ids = [self.resolve_item_id(i) for i in ids]
        if dist: # include distances with ids
            doc_ids = list(zip(doc_ids, dists))
        return self.uniq(doc_ids)

    def find_similar_to_item (self, i, n=10, dist=False):
        """Return items similar to the i-th item in the index in a
            descending order of similarity.
        
        Args:
            qi (integer): Item index. If number of items in the index
                are N, 0 < i < N
            n (int, optional): Number of items to return.
            dist (bool, optional): Whether distances to be included
                along with the returned items
        
        Returns:
            list: Similar items as a list of item ids (if dist=False),
                or tuples (item_id, distance) if dist=True.
        """
        ids, dists = self.index.get_nns_by_item(i, n, -1, True)
        doc_ids = [self.resolve_item_id(i) for i in ids]
        if dist: # include distances with ids
            doc_ids = list(zip(doc_ids, dists))
        return self.uniq(doc_ids)

    def find_similar (self, value, n=10, dist=False):
        """Find n items similar to a vector or the i-th item.

        This function is supposed to be convenient router, which checks
        whether the supplied argument `value` is an item number or a
        vector, then calls one of the functions `find_similar_to_item`
        or `find_similar_to_vector`. 
        
        Args:
            value (numpy.ndarray or int): Query vector or index of the
                query item in the index (like, find items similar to 
                the third item in the index)
            n (int, optional): Number of items to return.
            dist (bool, optional): Whether distances to be included
                along with the returned items
        
        Returns:
            list: Similar items as a list of item ids (if dist=False),
                or tuples (item_id, distance) if dist=True.
        """
        if type(value) is int:
            return self.find_similar_to_item(value, n, dist)
        elif type(value) is np.ndarray or type(value) is list:
            return self.find_similar_to_vector(value, n, dist)
        else:
            return None

    def resolve_item_id (self, i):
        """Summary
        
        Args:
            i (int): Item id, that is, the index at which the item is
                stored in the index.
        
        Returns:
            str: The identification for the item stored in the index's
                items list, e.g., a patent number.
        """
        return self.items[i]

    def uniq (self, arr):
        """Return a list of unique elements while preserving the order.

        If the elements are tuples, the first element is compared for
        duplicacy.
        
        Args:
            arr (list): A list of primitives or tuples
        
        Returns:
            list: A list of unique elements.
        """
        unique = [arr[0]]
        if type(arr[0]) is tuple:
            for i in range(1, len(arr)):
                if arr[i][0] != unique[-1][0]:
                    unique.append(arr[i])
        else:
            for i in range(1, len(arr)):
                if arr[i] != unique[-1]:
                    unique.append(arr[i])
        return unique
