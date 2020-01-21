from pymongo import MongoClient
client = MongoClient('localhost', 27017)
import json
import numpy as np
import re
import os
from annoy import AnnoyIndex
__dirname = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

word_index = AnnoyIndex(256, metric='angular')
word_index.load(__dirname + '/models/wv.ann')
vocab = json.load(open(__dirname + '/models/wv.ann.items.json', 'r'))
dictionary = json.load(open(__dirname + '/models/wv.ann.dict.json', 'r'))

stopword_list = ['a', 'about', 'above', 'accompanying', 'accomplish', 'accomplished', 'accomplishes', 'accomplishing', 'accordance', 'according', 'accordingly', 'achieve', 'achieved', 'achievement', 'achieves', 'achieving', 'additionally', 'advantage', 'advantageous', 'advantageously', 'advantages', 'after', 'all', 'along', 'also', 'although', 'among', 'an', 'and', 'and/or', 'any', 'are', 'art', 'as', 'aspect', 'aspects', 'assume', 'assumed', 'assumes', 'assuming', 'assumption', 'assumptions', 'at', 'basis', 'be', 'because', 'been', 'being', 'below', 'but', 'by', 'can', 'cause', 'caused', 'causes', 'causing', 'certain', 'comprise', 'comprised', 'comprises', 'comprising', 'could', 'currently', 'describe', 'described', 'describes', 'description', 'desired', 'detail', 'detailed', 'detailing', 'details', 'disclose', 'disclosed', 'discloses', 'disclosing', 'discuss', 'discussed', 'discussion', 'do', 'does', 'e.g', 'either', 'embodied', 'embodiment', 'embodiments', 'embody', 'etc', 'example', 'exemplary', 'fig', 'fig', 'figure', 'figure', 'figures', 'first', 'for', 'from', 'function', 'function', 'functionality', 'functioning', 'functions', 'functions', 'further', 'general', 'given', 'has', 'have', 'having', 'hereafter', 'herein', 'hereinafter', 'how', 'however', 'i.e', 'if', 'illustrate', 'illustrated', 'illustrates', 'illustration', 'implement', 'implementation', 'implemented', 'implementing', 'implements', 'in', 'include', 'include', 'included', 'includes', 'including', 'information', 'input', 'into', 'invent', 'invented', 'invention', 'inventions', 'inventors', 'invents', 'is', 'it', 'its', 'known', 'made', 'main', 'main', 'make', 'makes', 'making', 'manner', 'may', 'means', 'method', 'methods', 'might', 'must', 'noted', 'occur', 'occurred', 'occurring', 'occurs', 'of', 'on', 'one', 'or', 'ought', 'over', 'particular', 'perhaps', 'plural', 'plurality', 'possible', 'possibly', 'present', 'presently', 'prior', 'provide', 'provided', 'provides', 'providing', 'purpose', 'purposed', 'purposes', 'regard', 'relate', 'related', 'relates', 'relating', 'said', 'should', 'shown', 'similar', 'since', 'skill', 'skilled', 'so', 'some', 'step', 'steps', 'such', 'suitable', 'taught', 'teach', 'teaches', 'teaching', 'that', 'the', 'their', 'them', 'then', 'there', 'thereafter', 'thereby', 'therefore', 'therefrom', 'therein', 'thereof', 'thereon', 'therefor', 'these', 'they', 'third', 'this', 'those', 'though', 'through', 'thus', 'to', 'under', 'until', 'upon', 'use', 'used', 'uses', 'using', 'utilizes', 'various', 'very', 'was', 'we', 'well', 'when', 'where', 'whereby', 'wherein', 'whether', 'which', 'while', 'will', 'with', 'within', 'would', 'yet']
stopword_dict = {}
for word in stopword_list:
    stopword_dict[word] = 1

def calc_confidence_score(vectors):
    norms_squared = 0.00001 + (vectors * vectors).sum(axis=1, keepdims=True)
    sims = np.dot(vectors, vectors.T) / norms_squared
    std = np.std(sims.sum(axis=1, keepdims=False))
    if std < 25:
        return 'High'
    elif std > 25 and std < 35:
        return 'Medium'
    else:
        return 'Low'

def is_cpc_code (item):
    if not isinstance(item, str):
        return False
    pattern = r'^[ABCDEFGHY]\d\d[A-Z]\d+\/\d+$'
    return True if re.fullmatch(pattern, item) else False


def is_patent_number (item):
    if not isinstance(item, str):
        return False
    pattern = r'^[A-Z]{2}\d+[A-Z]\d?$'
    return True if re.fullmatch(pattern, item) else False


def is_generic(word):
    if word in stopword_list:
        return True
    else:
        return False


def synonyms(word, n=10):
    if not word in dictionary:
        return [word]

    i = dictionary[word]
    ns = word_index.get_nns_by_item(i, n, 100000)
    syns = [vocab[n] for n in ns]
    return syns


def n_docs_from(db, coll, n):
    docs = []
    cursor = client[db][coll].aggregate([{'$sample': { 'size': n }}])
    while cursor.alive:
        docs.append(cursor.next())
    return docs



def n_abstracts_from(db, coll, n):
    docs = n_docs_from(db, coll, n)
    abstracts = []
    for doc in docs:
        if 'abstract' in doc:
            abstracts.append(doc['abstract'])
    return abstracts



def n_titles_from(db, coll, n):
    docs = n_docs_from(db, coll, n)
    titles = []
    for doc in docs:
        if 'title' in doc:
            titles.append(doc['title'])
    return titles



def get_vocab(min_doc_freq=1):
    with open('/home/ubuntu/pqai/ind/lib/full_bib_vocab.json', 'r') as file:
        word_freq = json.loads(file.read())
    vocab = ['_pad_', '_oov_', '_sod_', '_eod_']
    dictionary = {
        '_pad_': 0,    # padding
        '_oov_': 1,    # out-of-vocabulary
        '_sod_': 2,    # start of document
        '_eod_': 3     # end of document
    }
    for word in word_freq:
        if word_freq[word] >= min_doc_freq:
            dictionary[word] = len(vocab)
            vocab.append(word)
    return vocab, dictionary



def fixed_length_sparse_vector(text, dictionary, length, add_sod=False, add_eod=False, tokenizer="[a-z]+"):
    vec = []
    if add_sod:
        vec.append(dictionary['_sod_'])
    words = re.findall(tokenizer, text.lower())
    
    l = length if add_eod == False else length-1
    
    pointer = 0
    while len(vec) < l and pointer < len(words):
        word = words[pointer]
        if word in dictionary:
            vec.append(dictionary[word])
        else:
            vec.append(dictionary['_oov_'])
        pointer += 1
    
    if add_eod:
        vec.append(dictionary['_eod_'])
        
    while len(vec) < length:
        vec.append(dictionary['_pad_'])

    return vec


def get_sentences(text):
    sentences = []
    paragraphs = get_paragraphs(text)
    ends = r"\b(etc|viz|fig|FIG|Fig|e\.g|i\.e|Nos|Vol|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Ser|Pat|no|No|Mr|pg|Pg|figs|FIGS|Figs)$"
    for paragraph in paragraphs:
        chunks = re.split("\.\s+", paragraph)
        i = 0
        while i < len(chunks):
            chunk = chunks[i]
            if re.search(ends, chunk) and i < len(chunks)-1:
                chunks[i] = chunk + '. ' + chunks[i+1]
                chunks.pop(i+1)
            elif i < len(chunks)-1:
                chunks[i] = chunks[i] + '.'
            i += 1
        for sentence in chunks:
            sentences.append(sentence)
    return sentences


def get_paragraphs(text):
    return re.split("\n+", text)


def cosine_dist(a, b):
    dot = np.dot(a, b)
    if dot == 0.0:
        return dot
    else:
        return dot / (np.linalg.norm(a) * np.linalg.norm(b))