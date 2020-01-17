cpc_index = AnnoyIndex(256, metric='angular')
cpc_index.load(models_dir + 'cpc_vectors_256d.ann')
cpc_vectors = np.load(models_dir + 'cpc_vectors_256d.npy')
cpc_vocab = json.load(open(models_dir + 'cpc_vectors_256d.ann.items.json', 'r'))
cpc_dict = {}
for i, cpc in enumerate(cpc_vocab):
    cpc_dict[cpc] = i
print('Loaded CPC model')

base_dir = str(Path(__file__).parent.resolve())
data_dir = base_dir + '/data/'
models_dir = base_dir + '/models/'

def avg_cpc_vec(cpcs):
    vec = np.zeros(256)
    count = 0
    for cpc in cpcs:
        if cpc in cpc_dict:
            m = cpc_dict[cpc]
            vec += cpc_vectors[m]
            count += 1
    if count > 0:
        vec /= count
    return vec
 