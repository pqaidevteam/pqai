import numpy as np
from annoy import AnnoyIndex
import json
from os.path import isfile
from core.vectorizer import vectorize

from config.config import indexes_dir
DIMS = 768

index_ids = [
    'A01B', 'A01C', 'A01D', 'A01F', 'A01G', 'A01H', 'A01J', 'A01K', 'A01L',
    'A01M', 'A01N', 'A21B', 'A21C', 'A21D', 'A22B', 'A22C', 'A23B', 'A23C',
    'A23D', 'A23F', 'A23G', 'A23J', 'A23K', 'A23L', 'A23N', 'A23P', 'A23V',
    'A24B', 'A24C', 'A24D', 'A24F', 'A41B', 'A41C', 'A41D', 'A41F', 'A41G',
    'A41H', 'A42B', 'A42C', 'A43B', 'A43C', 'A43D', 'A44B', 'A44C', 'A45B',
    'A45C', 'A45D', 'A45F', 'A46B', 'A46D', 'A47B', 'A47C', 'A47D', 'A47F',
    'A47G', 'A47H', 'A47J', 'A47K', 'A47L', 'A61B', 'A61C', 'A61D', 'A61F',
    'A61G', 'A61H', 'A61J', 'A61K', 'A61L', 'A61M', 'A61N', 'A61P', 'A61Q',
    'A62B', 'A62C', 'A62D', 'A63B', 'A63C', 'A63D', 'A63F', 'A63G', 'A63H',
    'A63J', 'B01D', 'B01F', 'B01J', 'B01L', 'B02B', 'B02C', 'B03B', 'B03C',
    'B03D', 'B04B', 'B04C', 'B05B', 'B05C', 'B05D', 'B06B', 'B07B', 'B07C',
    'B08B', 'B09B', 'B09C', 'B21B', 'B21C', 'B21D', 'B21F', 'B21H', 'B21J',
    'B21K', 'B21L', 'B22C', 'B22D', 'B22F', 'B23B', 'B23C', 'B23D', 'B23F',
    'B23G', 'B23H', 'B23K', 'B23P', 'B23Q', 'B24B', 'B24C', 'B24D', 'B25B',
    'B25C', 'B25D', 'B25F', 'B25G', 'B25H', 'B25J', 'B26B', 'B26D', 'B26F',
    'B27B', 'B27C', 'B27D', 'B27F', 'B27G', 'B27K', 'B27L', 'B27M', 'B27N',
    'B28B', 'B28C', 'B28D', 'B29B', 'B29C', 'B29D', 'B29K', 'B29L', 'B30B',
    'B31B', 'B31D', 'B31F', 'B32B', 'B33Y', 'B41C', 'B41F', 'B41J', 'B41K',
    'B41L', 'B41M', 'B41N', 'B41P', 'B42B', 'B42C', 'B42D', 'B42F', 'B43K',
    'B43L', 'B43M', 'B44B', 'B44C', 'B44D', 'B44F', 'B60B', 'B60C', 'B60D',
    'B60F', 'B60G', 'B60H', 'B60J', 'B60K', 'B60L', 'B60M', 'B60N', 'B60P',
    'B60Q', 'B60R', 'B60S', 'B60T', 'B60V', 'B60W', 'B60Y', 'B61B', 'B61C',
    'B61D', 'B61F', 'B61G', 'B61H', 'B61K', 'B61L', 'B62B', 'B62D', 'B62H',
    'B62J', 'B62K', 'B62L', 'B62M', 'B63B', 'B63C', 'B63G', 'B63H', 'B63J',
    'B64B', 'B64C', 'B64D', 'B64F', 'B64G', 'B65B', 'B65C', 'B65D', 'B65F',
    'B65G', 'B65H', 'B66B', 'B66C', 'B66D', 'B66F', 'B67B', 'B67C', 'B67D',
    'B68B', 'B68C', 'B68G', 'B81B', 'B81C', 'B82Y', 'C01B', 'C01C', 'C01D',
    'C01F', 'C01G', 'C01P', 'C02F', 'C03B', 'C03C', 'C04B', 'C05B', 'C05C',
    'C05D', 'C05F', 'C05G', 'C06B', 'C06C', 'C06D', 'C07B', 'C07C', 'C07D',
    'C07F', 'C07G', 'C07H', 'C07J', 'C07K', 'C08B', 'C08C', 'C08F', 'C08G',
    'C08H', 'C08J', 'C08K', 'C08L', 'C09B', 'C09C', 'C09D', 'C09G', 'C09J',
    'C09K', 'C10B', 'C10C', 'C10G', 'C10J', 'C10K', 'C10L', 'C10M', 'C10N',
    'C11B', 'C11C', 'C11D', 'C12C', 'C12G', 'C12H', 'C12M', 'C12N', 'C12P',
    'C12Q', 'C12R', 'C12Y', 'C13B', 'C13K', 'C14B', 'C14C', 'C21B', 'C21C',
    'C21D', 'C22B', 'C22C', 'C22F', 'C23C', 'C23F', 'C23G', 'C25B', 'C25C',
    'C25D', 'C25F', 'C30B', 'C40B', 'D01D', 'D01F', 'D01G', 'D01H', 'D02G',
    'D02J', 'D03C', 'D03D', 'D03J', 'D04B', 'D04C', 'D04D', 'D04H', 'D05B',
    'D05C', 'D06B', 'D06C', 'D06F', 'D06H', 'D06L', 'D06M', 'D06N', 'D06P',
    'D06Q', 'D07B', 'D10B', 'D21B', 'D21C', 'D21D', 'D21F', 'D21G', 'D21H',
    'D21J', 'E01B', 'E01C', 'E01D', 'E01F', 'E01H', 'E02B', 'E02D', 'E02F',
    'E03B', 'E03C', 'E03D', 'E03F', 'E04B', 'E04C', 'E04D', 'E04F', 'E04G',
    'E04H', 'E05B', 'E05C', 'E05D', 'E05F', 'E05G', 'E05Y', 'E06B', 'E06C',
    'E21B', 'E21C', 'E21D', 'E21F', 'F01B', 'F01C', 'F01D', 'F01K', 'F01L',
    'F01M', 'F01N', 'F01P', 'F02B', 'F02C', 'F02D', 'F02F', 'F02G', 'F02K',
    'F02M', 'F02N', 'F02P', 'F03B', 'F03C', 'F03D', 'F03G', 'F03H', 'F04B',
    'F04C', 'F04D', 'F04F', 'F05B', 'F05D', 'F15B', 'F15C', 'F15D', 'F16B',
    'F16C', 'F16D', 'F16F', 'F16G', 'F16H', 'F16J', 'F16K', 'F16L', 'F16M',
    'F16N', 'F16P', 'F16T', 'F17C', 'F17D', 'F21K', 'F21L', 'F21S', 'F21V',
    'F21W', 'F21Y', 'F22B', 'F23C', 'F23D', 'F23G', 'F23J', 'F23K', 'F23L',
    'F23M', 'F23N', 'F23Q', 'F23R', 'F24B', 'F24C', 'F24D', 'F24F', 'F24H',
    'F24J', 'F24S', 'F24T', 'F24V', 'F25B', 'F25C', 'F25D', 'F25J', 'F26B',
    'F27B', 'F27D', 'F28B', 'F28C', 'F28D', 'F28F', 'F28G', 'F41A', 'F41B',
    'F41C', 'F41F', 'F41G', 'F41H', 'F41J', 'F42B', 'F42C', 'F42D', 'G01B',
    'G01C', 'G01D', 'G01F', 'G01G', 'G01H', 'G01J', 'G01K', 'G01L', 'G01M',
    'G01N', 'G01P', 'G01Q', 'G01R', 'G01S', 'G01T', 'G01V', 'G01W', 'G02B',
    'G02C', 'G02F', 'G03B', 'G03C', 'G03D', 'G03F', 'G03G', 'G03H', 'G04B',
    'G04C', 'G04F', 'G04G', 'G04R', 'G05B', 'G05D', 'G05F', 'G05G', 'G06E',
    'G06F', 'G06G', 'G06J', 'G06K', 'G06M', 'G06N', 'G06Q', 'G06T', 'G07B',
    'G07C', 'G07D', 'G07F', 'G07G', 'G08B', 'G08C', 'G08G', 'G09B', 'G09C',
    'G09F', 'G09G', 'G10C', 'G10D', 'G10F', 'G10G', 'G10H', 'G10K', 'G10L',
    'G11B', 'G11C', 'G16H', 'G21B', 'G21C', 'G21D', 'G21F', 'G21G', 'G21H',
    'G21K', 'G21Y', 'H01B', 'H01C', 'H01F', 'H01G', 'H01H', 'H01J', 'H01K',
    'H01L', 'H01M', 'H01P', 'H01Q', 'H01R', 'H01S', 'H01T', 'H02B', 'H02G',
    'H02H', 'H02J', 'H02K', 'H02M', 'H02N', 'H02P', 'H02S', 'H03B', 'H03C',
    'H03D', 'H03F', 'H03G', 'H03H', 'H03J', 'H03K', 'H03L', 'H03M', 'H04B',
    'H04H', 'H04J', 'H04K', 'H04L', 'H04M', 'H04N', 'H04Q', 'H04R', 'H04S',
    'H04W', 'H05B', 'H05F', 'H05G', 'H05H', 'H05K', 'Y02A', 'Y02B', 'Y02D',
    'Y02E', 'Y02P', 'Y02T', 'Y02W', 'Y04S', 'Y10S', 'Y10T'
]

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
        self.search_depth = 1000 # No. of nodes inspected during search

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