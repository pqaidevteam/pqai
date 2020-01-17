# load patent indexes and items
indexes = {}
for indexid in ['H04W', 'G06T', 'G06N', 'Y02E']:
    index = AnnoyIndex(256, metric='angular')
    index_file = data_dir + '{}.ann'.format(indexid)
    vocab_file = data_dir + '{}.ann.items.json'.format(indexid)
    index.load(index_file)
    patlist = json.load(open(vocab_file, 'r'))
    print(indexid, len(patlist), index.get_n_items())
    assert len(patlist) == index.get_n_items()
    indexes[indexid] = (index, patlist)


def get_index_by_id (indexid):
    if indexid not in indexes:
        print("{} not found in indexes".format(indexid))
        return None
    return indexes[indexid]



def n_unique(arr, n):
    obj = {}
    new_arr = []
    for pair in arr:
        if not pair[0] in obj:
            obj[pair[0]] = True
            new_arr.append(pair)
    return new_arr[:n]