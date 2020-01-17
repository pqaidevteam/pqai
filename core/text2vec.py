# load word vectors from Annoy index
word_index = AnnoyIndex(256, metric='angular')
word_index.load(models_dir + 'wv.ann')
print('Words: ',  word_index.get_n_items())
print('Successfully loaded word index')


import re
import numpy as np
import json
from sklearn.decomposition import TruncatedSVD

remove_pc = False
alpha = 0.015

import os
__dirname = os.path.dirname(__file__)

models_dir = __dirname + '/../models/'

dictionary = json.load(open(models_dir + 'glove-dictionary.json'))
We = np.load(models_dir + 'glove-We.npy')
# Ww = np.load(models_dir + 'glove-Ww.npy')

def get_word_weights():
    global dictionary
    global alpha
    df = json.load(open(models_dir + '/dfs.json', 'r'))
    print('alpha =', alpha)
    N = df['the'] + 1
    weights = {}
    for word in df:
        n = df[word]
        p_word = n/N
        w_word = alpha / (alpha + p_word)
        weights[word] = w_word
    Ww = np.ones(len(dictionary))
    for word in dictionary:
        i = dictionary[word]
        if word in weights:
            Ww[i] = weights[word]
        else:
            Ww[i] = 1.0
    return Ww

Ww = get_word_weights()

def tokenize(sent):
    words = re.findall(r'[a-z]+', sent.lower())
    return words

def remove_unk(words, dictionary):
    return [word for word in words if word in dictionary]

def uniq(words):
    return list(set(words))    # changes word order

def idxs(words, dictionary):
    x = [dictionary[word] for word in words]
    return x

def compose(x, We, Ww):
    X = np.zeros((len(x), We.shape[1]))
    for i in range(len(x)):
        n = x[i]    # word index
        X[i,:] = (We[n]*Ww[n]) / len(x)
    if remove_pc == True:
        svd = TruncatedSVD(n_components=1, n_iter=7, random_state=0)
        svd.fit(X)
        pc = svd.components_
        X = (X - X.dot(pc.transpose()) * pc)
    y = X.sum(axis=0)
    return y

def embed(sent, unique=True):
    global We
    global Ww
    global dictionary
    words = tokenize(sent)
    words = remove_unk(words, dictionary)
    if unique:
        words = uniq(words)
    x = idxs(words, dictionary)
    if len(x) == 0:
        return np.array([0.00001]*We.shape[1])
    vec = compose(x, We, Ww)
    return vec

# vocab = list of words in same sequence
# as they are indexed in Annoy
vocab = json.load(open(models_dir + 'wv.ann.items.json', 'r'))
dictionary = json.load(open(models_dir + 'wv.ann.dict.json', 'r'))

# Spacy - used for lemmatization
print('Loading spacy...')
import spacy
nlp = spacy.load('en_core_web_sm')
print('Successfully loaded spacy.')


def encode(in_data):
    if type(in_data) == str:
        string = in_data
        return sent2vec.embed(string)
    elif type(in_data) == list and type(in_data[0]) == str:
        X = [sent2vec.embed(string)
            for string in in_data if len(string) >= 25]
        X = np.array(X)
        return X
    else:
        return None

def encode_query(query):
    b = np.zeros(256)
    words = re.findall('[a-z]+', query)
    for word in words:
        a = encode(query)
        a /= np.linalg.norm(a)
        b += a
    return b

# Encoder - used for converting a text snippet (max_len=80 words)
# into a vector of 512 dimensions
# print('Loading encoder...')
# encoder_model_path = __dirname + '/models/encode_sent_512d_aug_27.h5'
# encoder_vocab_path = __dirname + '/models/encode_sent_512d_aug_27.dict.json'
# encoder = keras.models.load_model(encoder_model_path)
# with open(encoder_vocab_path, 'r') as file:
#     encoder_dict = json.loads(file.read())
# print('Succesfully loaded encoder...')


# to run the model on flask (which uses multiple threads)
# force the keras model to use the same thread
# (this variable is used when predicting with the model)
# global graph
# graph = tf.get_default_graph()


# def encoder_fn(in_data):
#     if type(in_data) == str:
#         int_arr = gf.fixed_length_sparse_vector(in_data, encoder_dict, 80)
#         with graph.as_default():
#             vector = encoder.predict(np.array([int_arr]))[0]
#         return vector
#     elif type(in_data) == list and type(in_data[0]) == str:
#         X = [gf.fixed_length_sparse_vector(sent, encoder_dict, 80)
#                 for sent in in_data if len(sent) >= 25]
#         with graph.as_default():
#             vectors = encoder.predict(np.array(X))
#             return vectors
#     else:
#         return None