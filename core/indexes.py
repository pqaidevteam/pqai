import numpy as np
from annoy import AnnoyIndex
import json
from os.path import isfile
from core.vectorizer import vectorize

from config.config import indexes_dir
DIMS = 768

index_ids = [
    'G01B', 'G03G', 'G07B', 'G21B', 'H02H', 'H04R', 'Y02D', 'G01R',
    'G06D', 'G10B', 'H01H', 'H03J', 'G01C', 'G03H', 'G07C', 'G21C',
    'H02J', 'H04S', 'Y02E', 'G01S', 'G06E', 'G10C', 'H01J', 'H03K',
    'G01D', 'G04B', 'G07D', 'G21D', 'H02K', 'H04W', 'G01T', 'G06F',
    'G10D', 'H01K', 'H03L', 'G01F', 'G04C', 'G07F', 'G21F', 'H02M',
    'Y02P', 'G01V', 'G06G', 'G10F', 'H01L', 'H03M', 'H05B', 'G01G',
    'G04D', 'G07G', 'G21G', 'H02N', 'Y02T', 'G01W', 'G06J', 'G10G',
    'H01M', 'H04B', 'H05C', 'G01H', 'G04F', 'G08B', 'G21H', 'H02P',
    'Y02W', 'G02B', 'G06K', 'G10H', 'H01P', 'H04H', 'H05F', 'G01J',
    'G04G', 'G08C', 'G21J', 'H02S', 'Y04S', 'G02C', 'G06M', 'G10K',
    'H01Q', 'H04J', 'H05G', 'G01K', 'G04R', 'G08G', 'G21K', 'H03B',
    'Y10S', 'G02F', 'G06N', 'G10L', 'H01R', 'H04K', 'H05H', 'G01L',
    'G05B', 'G09B', 'G21Y', 'H03C', 'Y10T', 'G03B', 'G06N', 'G11B',
    'H01S', 'H04L', 'H05K', 'G01M', 'G05D', 'G09C', 'H01B', 'H03D',
    'G03C', 'G06Q', 'G11C', 'H01T', 'H04M', 'Y02A', 'G01N', 'G05F',
    'G09D', 'H01C', 'H03F', 'G03D', 'G06T', 'G12B', 'H02B', 'H04N',
    'Y02B', 'G01P', 'G05G', 'G09F', 'H01F', 'H03G', 'G03F', 'G06T',
    'G16H', 'H02G', 'H04Q', 'Y02C', 'G01Q', 'G06C', 'G09G', 'H01G',
    'H03H']

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
    items_file = f"{indexes_dir}{index_id}.items.json"
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
        self.index = AnnoyIndex(DIMS, metric='angular')
        self.index.load(ann_file)
        self.n_items = self.index.get_n_items()
        self.items = json.load(open(json_file, 'r'))
        self.search_depth = 100000 # No. of nodes inspected during search

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
        ids, dists = self.index.get_nns_by_vector(query_vec, n, self.search_depth, True)
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
        ids, dists = self.index.get_nns_by_item(i, n, self.searh_depth, True)
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

    def run_text_query(self, query, n=10, dist=True):
        """Search with a text query.
        
        Args:
            query (str): Query
            n (int, optional): Number of results to return
            dist (bool, optional): Whether distances (similarities) are
                to be returned along with result ids.
        
        Returns:
            list: Similar items as a list of item ids (if dist=False),
                or tuples (item_id, distance) if dist=True.
        """
        query_vector = vectorize(query)
        results = self.find_similar(query_vector, n, True)
        return results