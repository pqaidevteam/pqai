import numpy as np
import math

from core.encoders import EmbeddingMatrix
from core.encoders import BagOfEntitiesEncoder, BagOfVectorsEncoder
from core.representations import BagOfVectors

class Ranker:

    def __init__(self, scoring_fn, metric_type='similarity'):
        self.scoring_fn = scoring_fn
        self.metric_type = metric_type

    def score(self, query, document):
        """Calculate numerical similarity between query and document.
        
        Args:
            query (str): Text query (reference text)
            document (str): Text document
        
        Returns:
            float: Similarity score
        """
        return self.scoring_fn(query, document)

    def rank(self, query, documents):
        """Get ranks for `documents` on the basis of similarity with
            `query`.
        
        Args:
            query (str): The query (reference text)
            documents (list): Text documents
        
        Returns:
            list: Ranks for each of the documents, e.g., [2, 0, 1] means
                the document at index 0 in the input list `documents` has
                rank 2 (least similar) and document at index 1 is most
                similar. Note that the calling function has to sort the
                actual document list.
        """
        scores = [self.scoring_fn(query, document) for document in documents]
        ranks = np.argsort(scores)
        if self.metric_type == 'similarity':
            return ranks[::-1]
        else:
            return ranks

class MatchPyramidRanker(Ranker):

    """An implementation of text similarity scoring algorithm, Pang et al. 2016
    """
    
    def __init__(self):
        from core.matchpyramid import  calculate_similarity
        import re # needed because of an issue in MatchZoo library
        super().__init__(calculate_similarity, 'similarity')

class ConvKNRMRanker(Ranker):

    def __init__(self):
        pass

from core.representations import Text, Interaction
from core.representations import embeddings

class CustomRanker(Ranker):

    def __init__(self):
        self._interaction = Interaction()
        self._interaction.metric = 'cosine'
        self._interaction.amplify = True
        self._interaction.reinforce = False
        self._interaction.context = False
        self._interaction.window = 10
        self._interact = self._interaction.interact
        super().__init__(self.similarity, 'similarity')

    def similarity(self, query, doc):
        query_tokens = Text(query).to_tokens()
        doc_tokens = Text(doc).to_tokens()
        nq = len(query_tokens)
        nd = max(1, len(doc_tokens))
        doc_length_surplus = max(1, nd/nq)
        doc_length_penalty_factor = 1 + 0.5*math.sqrt(doc_length_surplus)
        Q = query_tokens.to_vector_sequence(embeddings)
        D = doc_tokens.to_vector_sequence(embeddings)
        query_term_matches = self._interact(Q, D).maxpool()
        sifs = embeddings.sifs
        query_term_weights = [(sifs[word] if word in sifs else 1.0)
                                    for word in query_tokens]
        query_term_weights *= 1 - Q.redundancy_vector
        query_term_matches *= query_term_weights
        score = query_term_matches.sum()
        if query != doc:
            score /= self.similarity(query, query)
            score /= doc_length_penalty_factor
        return score

class ConceptMatchRanker(Ranker):

    """Ranking algorithm that scores text similarity by extracting concepts
    (entities) from a piece of text, then comparing their embeddings
    with word movers distance.
    """
    
    def __init__(self):
        super().__init__(self._get_similarity, 'distance')
        entities_file = "/home/ubuntu/exp/data/entities.vocab.txt"
        vectors_file = "/home/ubuntu/exp/data/entities.vectors.npy"
        ent_embs = EmbeddingMatrix.from_txt_npy(entities_file, vectors_file)
        self._boe_encoder = BagOfEntitiesEncoder.from_vocab_file(entities_file)
        self._bov_encoder = BagOfVectorsEncoder(ent_embs)

    def _get_similarity(self, qry, doc):
        qry_boe = self._boe_encoder.encode(qry)
        doc_boe = self._boe_encoder.encode(doc)
        print(qry_boe)
        qry_rep = self._bov_encoder.encode(qry_boe)
        doc_rep = self._bov_encoder.encode(doc_boe)
        return BagOfVectors.wmd(qry_rep, doc_rep)