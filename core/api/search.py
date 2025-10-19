import json
import re
import numpy as np
import time
import threading
from typing import Optional
from pydantic import BaseModel, Field

from core.filters import FilterExtractor
from core.obvious import Combiner
from core.results import SearchResult
import core.remote as remote
import core.utils as utils
from core.documents import Patent
from core.snippet import SnippetExtractor
from core.vectorizers import SentBERTVectorizer

from services import vector_search as vector_search_srv

from config.config import (
    reranker_active,
    allow_incoming_extension_requests,
    allow_outgoing_extension_requests
)

from .base import APIRequest, NotAllowedError, ResourceNotFoundError

reranker = None
if reranker_active:
    from core.reranking import ConceptMatchRanker
    reranker = ConceptMatchRanker()

vectorize = SentBERTVectorizer().embed

if not vector_search_srv.ready():
    thread = threading.Thread(target=vector_search_srv.start)
    thread.start()
    while not vector_search_srv.ready():
        print("Waiting for vector search service to be ready...")
        time.sleep(1)


class SearchRequestSchema(BaseModel):
    q: str = Field(min_length=1)
    lq: str = Field(default='')
    offset: int = Field(default=0, ge=0)
    n: int = Field(default=10, ge=1, le=500)
    type: str = Field(default='patent', pattern=r'^(patent|npl|any)$')
    idx: Optional[str] = Field(default=None)
    snip: bool = Field(default=False)
    maps: bool = Field(default=False)
    after: Optional[str] = Field(default=None)
    before: Optional[str] = Field(default=None)
    dtype: str = Field(default='priority', pattern=r'^(publication|filing|priority)$')

class SearchRequest(APIRequest):
    _schema = SearchRequestSchema
    MAX_RES_LIMIT = 500
    MIN_SIMILARITY_THRESHOLD = 0.5

    def __init__(self, req_data):
        super().__init__(req_data)
        self.query = self.q
        self._n_results = self.n + self.offset
        self._filters = FilterExtractor.extract(self._params)

    def _serve(self):
        raise NotImplementedError

    def _format(self, results):
        arr = []
        for result in results:
            if isinstance(result, SearchResult):
                self._format_result(result)
                arr.append(result.json())
            elif hasattr(result, '__iter__'):
                for r in result:
                    self._format_result(r)
                arr.append([r.json() for r in result])
        return {
            'results': arr,
            'query': self.query,
            'latent_query': self.lq
        }

    def _format_result(self, result):
        if self.maps:
            try:
                result.mapping = SnippetExtractor.map(self.query, result.full_text)
            except Exception:
                result.mapping = None
        if self.snip:
            try:
                result.snippet = SnippetExtractor.extract_snippet(self.query, result.full_text)
            except Exception:
                result.snippet = None
        if result.type == 'patent':
            result.image = f'https://api.projectpq.ai/patents/{result.id}/thumbnails/1'

class SearchRequest102(SearchRequest):

    def _serve(self):
        results = self._search()
        if self._n_results < 100:
            results = self._rerank(results)
        results = results[:self._n_results]
        return results[self.offset:]

    def _search(self):
        query = re.sub(r'\`(\-[\w\*\?]+)\`', '', self.query)
        query = re.sub(r"\`", "", query)
        qvec = vectorize("[query] " + query)
        relevant, irrelevant = self._extract_feedback(self.lq)
        if relevant or irrelevant: # user feedback
            qvec = self._update_search_vector(qvec, relevant, irrelevant)

        results = []
        n = min(self._n_results, self.MAX_RES_LIMIT)
        m = max(25, n)
        while len(results) < n and m <= 2*self.MAX_RES_LIMIT:
            payload = {
                "vector": qvec.tolist(),
                "n_results": m,
                "type": self.type
            }

            # Run a vector search
            results = vector_search_srv.send(payload)
            results = [t for t in results if t[2] > self.MIN_SIMILARITY_THRESHOLD]
            results = self._deduplicate_by_score(results)
            results = self._filters.apply(results, m)

            if not results:
                break

            # Avoid looking for more results if the last one is a poor match
            if results[-1][2] <= self.MIN_SIMILARITY_THRESHOLD + 0.01:
                break

            m *= 2
        results = [SearchResult(*t) for t in results]
        results = self._deduplicate(results)
        return results[:n]

    def _update_search_vector(self, qvec, relevant, irrelevant):
        alpha = 1.0
        beta = 1.0
        gamma = 1.0

        if relevant:
            vr = np.array([vectorize(Patent(pn).abstract) for pn in relevant])
            vr_mean = np.mean(vr, axis=0)
            qvec = alpha*qvec + beta*vr_mean

        if irrelevant:
            vi = np.array([vectorize(Patent(pn).abstract) for pn in irrelevant])
            vi_mean = np.mean(vi, axis=0)
            qvec = qvec - gamma*vi_mean

        qvec = qvec / np.linalg.norm(qvec)
        return qvec

    def _extract_feedback(self, latent_query):
        try:
            lq_data = json.loads(latent_query)
        except Exception:
            return [], []

        if not isinstance(lq_data, dict):
            return [], []

        relevant = lq_data.get('relevant', [])
        irrelevant = lq_data.get('irrelevant', [])
        return relevant, irrelevant

    def _rerank(self, results):
        if not reranker:
            return results
        result_texts = [r.abstract for r in results]
        ranks = reranker.rank(self.query, result_texts)
        return [results[i] for i in ranks]

    def _deduplicate_by_score(self, triplets):
        if not triplets:
            return triplets

        epsilon = 0.000001
        first, subsequent = triplets[0], triplets[1:]
        output = [first]
        for this in subsequent:
            last = output[-1]
            diff_score = abs(last[2] - this[2])
            if  diff_score >= epsilon:
                output.append(this)
                continue

            # when scores are too close (likely family members), prefer an English-language member
            cc_this = this[0][:2]
            cc_last = last[0][:2]
            cc_pref = ['US', 'EP', 'GB', 'CA', 'AU', 'WO', 'SG', 'IN'] # native English abstracts
            cc_rank = {cc: i for i, cc in enumerate(cc_pref)}
            default_rank = len(cc_pref)
            if cc_this == cc_last:
                continue

            rank_this = cc_rank.get(cc_this, default_rank)
            rank_last = cc_rank.get(cc_last, default_rank)
            if rank_this < rank_last:
                output[-1] = this

        return output

    def _deduplicate(self, results):
        relevant, irrelevant = self._extract_feedback(self.lq)
        seen = set(relevant + irrelevant)
        results = [r for r in results if r.id not in seen]

        deduplicated = []
        titles = set()
        for result in results:
            if result.title is None: # defects in the database
                continue
            if result.title.lower() in titles:
                continue
            deduplicated.append(result)
            titles.add(result.title.lower())
        return deduplicated

    def _add_remote_results_to(self, local_results):
        if not allow_outgoing_extension_requests:
            return local_results
        remote_results = remote.search_extensions(self._params)
        return remote.merge([local_results, remote_results])

class SearchRequest103(SearchRequest):

    def _serve(self):
        docs = self._get_docs_to_combine()
        self._results102 = docs
        abstracts = [doc.abstract for doc in docs]
        combiner = Combiner(self.query, abstracts)
        n = max(50, self._n_results) # see SearchRequest102 for why max used
        index_pairs = combiner.get_combinations(n)
        combinations = [(docs[i], docs[j]) for i, j in index_pairs]
        combinations = combinations[:self._n_results]
        return combinations[self.offset:]

    def _get_docs_to_combine(self):
        params = {**self._params, 'n': 100, 'offset': 0, 'snip': 0, 'maps': 0}
        results = SearchRequest102(params).serve()['results']
        return [SearchResult(r['id'], r['index'], r['score']) for r in results]

class SearchRequestCombined102and103(SearchRequest103):

    def _serve(self):
        results103 = super()._search()
        results102 = self._results102[:self._n_results][self.offset:]
        results = self._merge_102_and_103_results(results102, results103)
        return results[:self._n_results][self.offset:]

    def _merge_102_and_103_results(self, results102, results103):
        results = []
        p1 = 0
        p2 = 0
        while (p1 < len(results102) and p2 < len(results103)):
            r1 = results102[p1]
            r2 = results103[p2]
            if (r1.score <= min(r2[0].score, r2[1].score)):
                results.append(r1)
                p1 += 1
            else:
                results.append(r2)
                p2 += 1
        results += results102[p1:] + results103[p2:]
        return results

class PatentRelatedRequestSchema(BaseModel):
    pn: str = Field(pattern=r'^[A-Z]{2,4}\d{4,11}[A-Z]\d?$')

class SimilarPatentsRequest(APIRequest):
    _schema = PatentRelatedRequestSchema

    def _serve(self):
        search_params = self._get_search_params(self.pn)
        return SearchRequest102(search_params).serve()

    def _get_search_params(self, pn):
        claim = Patent(pn).first_claim
        query = utils.remove_claim_number(claim)
        search_params = {'q': query, 'type': 'patent', 'n': 100}
        return search_params

    def _format(self, response):
        response['query'] = self.pn
        return response

class PatentPriorArtRequest(SimilarPatentsRequest):

    def _get_search_params(self, pn):
        search_params = super()._get_search_params(pn)
        search_params = {
            **search_params,
            'before': Patent(pn).priority_date,
            'dtype': 'priority'
        }
        print(search_params)
        return search_params

class IncomingExtensionRequest(SearchRequest102):

    def __init__(self, req_data):
        if not allow_incoming_extension_requests:
            msg = 'This server does not accept extension requests.'
            raise NotAllowedError(msg)
        else:
            super().__init__(req_data)