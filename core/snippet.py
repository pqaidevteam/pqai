import numpy as np
from random import randrange
import re
from core import utils
from core.highlighter import highlight as highlighter_fn

from core.vectorizers import SIFTextVectorizer
encoder_fn = SIFTextVectorizer().embed

from core.reranking import CustomRanker
ranker = CustomRanker()


class SnippetExtractor():

    MIN_SNIPPET_LENGTH = 50

    @classmethod
    def extract_snippet(cls, query, text, htl_on=False):
        sents = cls._get_mappable_sentences(text)
        idx = ranker.rank(query, sents)[0]
        before = ''
        center = sents[idx]
        after = ''
        if idx > 0:
            before = cls._last_few_words(sents[idx-1])
        if idx < len(sents)-1:
            after = cls._first_few_words(sents[idx+1])
        if htl_on:
            center = KeywordHighlighter.highlighter_fn(query, center)[0]
        snippet = before + center + after
        return snippet

    @classmethod
    def map(cls, query, text):
        elements = utils.get_elements(query)
        sents = cls._get_mappable_sentences(text)

        A = utils.normalize_rows(np.array([encoder_fn(e) for e in elements]))
        B = utils.normalize_rows(np.array([encoder_fn(e) for e in sents]))
        
        cosine_sims = np.dot(A, B.T)
        sent_idxs = cosine_sims.argmax(axis=1)
        
        mappings = []
        for i, element in enumerate(elements):
            mapping = {}
            j = sent_idxs[i]
            mapping['element'] = element
            mapping['mapping'] = sents[j]
            mapping['ctx_before'] = sents[j-1] if j-1 > 0 else ''
            mapping['ctx_after'] = sents[j+1] if j+1 < len(sents) else ''
            mapping['similarity'] = float(cosine_sims[i][j])
            mappings.append(mapping)
        return mappings

    @classmethod
    def _get_mappable_sentences(cls, text):
        sents = [sent for sent in utils.get_sentences(text)]
        sents = [sent for sent in sents if len(sent)>=cls.MIN_SNIPPET_LENGTH]
        return sents

    @classmethod
    def _last_few_words(cls, sent):
        num_words = randrange(5, 10)
        i = len(sent)-1
        n = 0
        while i > 0 and n < num_words:
            if sent[i] == ' ':
                n += 1
            i -= 1
        return '...' + sent[i+1:len(sent)] + ' '

    @classmethod
    def _first_few_words(cls, sent):
        num_words = randrange(2, 5)
        i = 0
        n = 0
        while i < len(sent) and n < num_words:
            if sent[i] == ' ':
                n += 1
            i += 1
        return ' ' + sent[0:i] + '...'
    