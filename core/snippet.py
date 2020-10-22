import numpy as np
from random import randrange
import re
from core import utils
from core.highlighter import highlight as highlighter_fn

from core.vectorizers import SIFTextVectorizer
text2vec = SIFTextVectorizer().embed

from core.reranking import CustomRanker, ConceptMatchRanker
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

        A = utils.normalize_rows(np.array([text2vec(e) for e in elements]))
        B = utils.normalize_rows(np.array([text2vec(e) for e in sents]))
        
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
        sents = [sent for sent in sents if re.match('[A-Z]', sent)]
        sents = [sent for sent in sents if not sent.endswith(':')]
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


class CombinationalMapping (SnippetExtractor):

    ranker = ConceptMatchRanker()

    def __init__(self, query, texts):
        self._texts = texts
        self._query = query
        self._elements = utils.get_elements(query)
        self._sents = [self._get_mappable_sentences(text) for text in texts]

    def map(self, table=False):
        mapping = [self._select_best(self._map_element_with_all(el))
                for el in self._elements]
        if not table:
            return mapping
        return self._format_as_table(mapping)

    def _map_element_with_all(self, el):
        n_texts = len(self._texts)
        return [self._map_element_with_ith(el, i) for i in range(n_texts)]

    def _map_element_with_ith(self, el, i):
        sents = self._sents[i]
        dists = [self.ranker.score(el, s) for s in sents]
        k = np.argmin(dists)
        dist = dists[k]
        return {
            'element': el,
            'doc': i,
            'mapping': sents[k],
            'ctx_before': sents[k-1] if k-1 > 0 else '',
            'ctx_after': sents[k+1] if k+1 < len(sents) else '',
            'similarity': dist
        }

    def _select_best(self, mappings):
        return sorted(mappings, key=lambda x: x['similarity'])[0]

    def _format_as_table(self, elmaps):
        table = []
        header = ['Elements'] + list(range(len(self._texts)))
        table.append(header)
        for elmap in elmaps:
            row = []
            row.append(elmap['element'])
            for i in range(len(self._texts)):
                if elmap['doc'] == i:
                    row.append(elmap['mapping'])
                else:
                    row.append('')
            table.append(row)
        return table
