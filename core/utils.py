"""
Shared utilities
"""

import re
from functools import lru_cache
import numpy as np

from config.config import models_dir

# Load stopwords
stopword_file = models_dir + 'stopwords.txt'
with open(stopword_file, 'r') as file:
    stopword_list = file.read().strip().splitlines()
stopword_dict = {word: 1 for word in stopword_list}


def calc_confidence_score(vecs):
    """Calculate a confidence score for the search results given the
    search result vectors.

    The confidence score is given on the basis of cosine similarity
    among the vectors. If the standard deviation of the similarity
    is high, confidence score is low, and if it is low, confidence
    score is high.

    Args:
        vecs (numpy.ndarray): 2d array where rows are vectors.

    Returns:
        str: One value from the set { 'High', 'Medium', 'Low'}
    """

    # calculate vector magnitudes for normalizing
    norms_squared = 0.00001 + (vecs*vecs).sum(axis=1, keepdims=True)

    # 2d matrix where element i,j is cosine similarity between
    # vectors i and j
    sims = np.dot(vecs, vecs.T) / norms_squared

    # calculate the standard deviation of cosine similarities
    std = np.std(sims.sum(axis=1, keepdims=False))

    # Use empirically determined thresholds for confidence score.
    if std < 25:
        return 'High'
    if 25 < std < 35:
        return 'Medium'
    return 'Low'


def is_cpc_code(item):
    """Check if an item is a Cooperative Patent Classification code.
    Should also work for IPC codes because they have same format.

    Examples:
    H04W52/00 => True
    H04W => False
    H04W005202 => False

    Args:
        item (str): String to be checked.

    Returns:
        bool: True if input string is a CPC code, False otherwise.
    """
    if not isinstance(item, str):
        return False
    pattern = r'^[ABCDEFGHY]\d\d[A-Z]\d+\/\d+$'
    return bool(re.fullmatch(pattern, item))


def is_patent_number(item):
    """Check if a string is a publication number for a patent or an
    application.

    Args:
        item (str): String to be checked.

    Returns:
        bool: True if the input string is a publication number, False
            otherwise.
    """
    if not isinstance(item, str):
        return False
    pattern = r'^[A-Z]{2}\d+[A-Z]\d?$'
    return bool(re.fullmatch(pattern, item))

def is_doc_id(item):
    return is_patent_number(item)

def is_generic(word):
    """Check if a given word is a generic word, e.g., 'the', 'of', etc.
    It is determined on the basis of a hand-picked list of keywords
    determined as generic words commonly used in patents.

    Args:
        word (str): Word to be checked.

    Returns:
        bool: True if the word is a generic word, False otherwise.
    """
    return word in stopword_dict

@lru_cache(maxsize=1000)
def get_sentences(text):
    """Split a given (English) text (possibly multiline) into sentences.

    Args:
        text (str): Text to be split into sentences.

    Returns:
        list: Sentences.
    """
    sentences = []
    paragraphs = get_paragraphs(text)
    ends = r"\b(etc|viz|fig|FIG|Fig|e\.g|i\.e|Nos|Vol|Jan|Feb|Mar|Apr|\
    Jun|Jul|Aug|Sep|Oct|Nov|Dec|Ser|Pat|no|No|Mr|pg|Pg|figs|FIGS|Figs)$"
    for paragraph in paragraphs:
        chunks = re.split(r"\.\s+", paragraph)
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
    r"""Split a text into paragraphs. Assumes paragraphs are separated
    by new line characters (\n).

    Args:
        text (str): Text to be split into paragraphs.

    Returns:
        list: Paragraphs.
    """
    return [s.strip() for s in re.split("\n+", text) if s.strip()]


def cosine_dist(a, b):
    """Find the cosine similarity between two vectors.

    Args:
        a (np.ndarray): The first vector
        b (np.ndarray): The second vector

    Returns:
        float: Cosine distance between the vectors
    """
    dot = np.dot(a, b)
    return dot/(np.linalg.norm(a) * np.linalg.norm(b)) if dot != 0.0 else 0.0


def tokenize(text, lowercase=True):
    """Get tokens (words) from given text.

    Args:
        text (str): Text to be tokenized (expects English text).
        lowercase (bool, optional): Whether the text should be
            lowercased before tokenization.

    Returns:
        list: Array of tokens.
    """
    if lowercase:
        text = text.lower()
    matches = re.findall(r'\b[a-z]+\b', text)
    return [] if matches is None else matches


def normalize_rows(M):
    return normalize_along_axis(M, 1)

def normalize_cols(M):
    return normalize_along_axis(M, 0)

def normalize_along_axis(M, axis):
    epsilon = np.finfo(float).eps
    norms = np.sqrt((M*M).sum(axis=axis, keepdims=True))
    norms += epsilon    # to avoid division by zero
    return M / norms


def remove_claim_number(claim_text):
    # TO DO: Write code for removing the number
    return claim_text


def get_elements(text):
    elements = []
    for paragraph in get_paragraphs(text):
        elements += get_sentences(paragraph)
    elements = [el.strip() for el in elements]
    elements = [el for el in elements
                if len(el) >= 3 and re.search('[A-Za-z]', el)]
    return elements


def get_external_link(pn):
    return f'https://patents.google.com/patent/{pn}/en'


def get_faln(authors): # faln = first author's last name
    if not authors:
        return "Unknown"

    name = authors[0]
    if ',' in name:                         # Doe, John
        faln = re.findall(r'\w+', name)[0]
    else:                                   # John Doe
        faln = re.findall(r'\w+', name)[-1]
    if len(authors) > 1:
        faln += ' et al.'
    return faln
