import numpy as np
from annoy import AnnoyIndex
import json

from config.config import indexes_dir

index_ids = ['H04W', 'G06T', 'G06N', 'Y02E']
indexes = {}

def init_index(index_id):
    """Load the .ann and .items.json file for the index.

    Employs lazy loading. Indexes are loaded when they are required to
    be searched by the index. Loading occurs only once; thereafter, the
    same loaded instance is used for searching.
    
    Args:
        index_id (str): Index identifier; the name with which the .ann
            file is saved.
    """
    ann_file = indexes_dir + index_id + '.ann'
    items_file = indexes_dir + index_id + '.ann.items.json'
    items_list = json.load(open(items_file, 'r'))
    annoy_index = AnnoyIndex(256, metric='angular')
    annoy_index.load(ann_file)

    global indexes
    indexes[index_id] = {
        'index_id': index_id,
        'vector_index': annoy_index,
        'items_list': items_list
    }


class Index():

    """An annoy index along with suitable names for its items.
    
    Attributes:
        index_id (str): Index's name, e.g., 'H04W'
        items_list (list): List of item "names", e.g., patent numbers
        vector_index (annoy.AnnoyIndex): The annoy index object, for
            details, check https://github.com/spotify/annoy
    """
    
    def __init__(self, index_id):
        """Load an index's data into the memory if not already loaded
            and return a pointer to it.
        
        Args:
            index_id (str): Index's name, e.g., 'H04W'
        """
        if index_id not in indexes: init_index(index_id)
        self.index_id = index_id
        self.vector_index = indexes[index_id]['vector_index']
        self.items_list = indexes[index_id]['items_list']

    def __getitem__(self, i):
        """Return vector for the i-th item.
        
        Args:
            i (int): Item index. If number of items in the index are N,
                0 < i < N
        
        Returns:
            numpy.ndarray: Item vector.
        """
        return self.vector_index.get_item_vector(i)

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
        index = self.vector_index
        ids, dists = index.get_nns_by_vector(query_vec, n, -1, True)
        N = len(ids)
        return ids if not dist else [(ids[i], dist[i]) for i in range(N)]

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
        index = self.vector_index
        ids, dists = index.get_nns_by_item(i, n, -1, True)
        N = len(ids)
        return ids if not dist else [(ids[j], dist[j]) for j in range(N)]

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
        return self.items_list[i]

    def resolve_item_ids (self, arr):
        """Summary
        
        Args:
            arr (list): List of item ids or tuples (item_id, dist)
        
        Returns:
            str: The identification for the item stored in the index's
                items list, e.g., a patent number.
        """
        if type(arr[0]) is int:
            return [self.resolve_item_id(i) for i in arr]
        elif type(arr[0]) is tuple and len(arr[0]) == 2:
            return [(self.resolve_item_id(i), dist) for (i, dist) in arr]
        else:
            return None