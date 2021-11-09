import numpy as np
from random import randrange
import re
from core import utils
from core.highlighter import highlight as highlighter_fn

from core.vectorizers import SIFTextVectorizer
text2vec = SIFTextVectorizer().embed

from core.reranking import CustomRanker, ConceptMatchRanker
ranker = CustomRanker()
conceptmatch_ranker = ConceptMatchRanker()

from core.documents import Document
from core.encoders import default_boe_encoder
from core.utils import get_sentences
from core.sensible_span_extractor import SensibleSpanExtractor
get_spans = SensibleSpanExtractor().return_ranked

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
            mapping['element'] = element
            try:
                multi_snippet = SubsentSnippetExtractor(element, text).extract()
                mapping['mapping'] = multi_snippet
                mapping['ctx_before'] = ''
                mapping['ctx_after'] = ''
                mapping['similarity'] = 0.0
            except Exception as e:
                traceback.print_exc()
                j = sent_idxs[i]
                mapping['mapping'] = sents[j]
                mapping['ctx_before'] = sents[j-1] if j-1 > 0 else ''
                mapping['ctx_after'] = sents[j+1] if j+1 < len(sents) else ''
                mapping['similarity'] = float(cosine_sims[i][j])
            mappings.append(mapping)

        return mappings

    @classmethod
    def _get_mappable_sentences(cls, text):
        sents = utils.get_sentences(text)
        sents = [s for s in sents if cls._is_mappable(s)]
        return sents

    @classmethod
    def _is_mappable(cls, sent):
        cond_1 = len(sent)>=cls.MIN_SNIPPET_LENGTH
        cond_2 = re.match('[A-Z]', sent)
        cond_3 = not sent.endswith(':')
        return True if (cond_1 and cond_2 and cond_3) else False

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


class SubsentSnippetExtractor():
    
    def __init__(self, query, doc):
        self.query = query
        self.doc = doc
    
    def extract(self):
        keyphrases = self._find_keyphrases_in_doc()
        subs = self._get_spliced_subsent_snippets(keyphrases)
        return self._join(subs)

    def _find_keyphrases_in_doc(self):
        query_concepts = self._extract_concepts(self.query)
        doc_concepts = self._extract_concepts(self.doc)
        keyphrases = []
        for concept in query_concepts:
            dists = [conceptmatch_ranker.score(concept, target) for target in doc_concepts]
            keyphrases.append(doc_concepts[np.argmin(dists)])
        return keyphrases

    def _get_spliced_subsent_snippets(self, matches):
        sents = get_sentences(self.doc)

        # select only sentences that do not contain references to drawings,
        # i.e., which do not have reference numeral (digits) in them
        sents = [s for s in sents if not re.search(r'\d{2,}', s)]

        sent_scores = [sum([1 for m in matches if m in s]) for s in sents]
        sent_ranked = [sents[i] for i in np.argsort(sent_scores)[::-1]]
        temp_str = ""
        subs = []
        for match in matches:
            if match in temp_str:
                continue

            for sent in sent_ranked:
                if match in sent:
                    sub = self._span_containing(match, sent)
                    temp_str += ' ...' + sub + '...'
                    subs.append(sub)
                    break
        return subs

    def _extract_concepts(self, text):
        target_concepts = set()
        for sent in get_sentences(text):
            for c in default_boe_encoder.encode(sent):
                target_concepts.add(c)
        return list(target_concepts)

    def _span_containing(self, entity, sent):
        spans = get_spans(sent)
        for span in spans:
            if entity in span:
                return span

    def _join(self, subs):
        return '...' + '... '.join(subs) + '...'
