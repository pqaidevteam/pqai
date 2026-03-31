import itertools
import json

SYNONYMS = {
    "drone": ["UAV", "unmanned aerial vehicle"],
    "navigation": ["guidance", "path planning"],
    "sensor fusion": ["multi-sensor integration"],
    "obstacle avoidance": ["obstacle detection", "collision avoidance"],
    "aerial mapping": ["surveying", "remote sensing"],
}


import re
from typing import List, Dict

def expand_synonyms(concept: str) -> List[str]:
    """
    Return a list of synonyms for a concept, including the original.
    Matches whole words/phrases for replacement.
    """
    terms = set([concept])
    for key, syns in SYNONYMS.items():
        pattern = re.compile(rf'\b{re.escape(key)}\b', re.IGNORECASE)
        if pattern.search(concept):
            for syn in syns:
                replaced = pattern.sub(syn, concept)
                terms.add(replaced)
    return list(terms)


def quote_term(term: str) -> str:
    """Quote term if it contains spaces or special characters."""
    if re.search(r'[^\w]', term):
        return f'"{term}"'
    return term


def generate_query_variations(concepts: List[str], max_queries: int = 10) -> List[str]:
    """
    Generate diverse, structured patent search queries from concepts.
    Adds field targeting (TTL, ABST, DESC) for patent search.
    """
    expanded = [expand_synonyms(c) for c in concepts]
    queries = set()

    # Field tags to rotate for diversity
    field_tags = ['TTL', 'ABST', 'DESC']

    def tag_terms(terms, tag_idx=0):
        # Cycle through field tags for each term
        return [f'{field_tags[(tag_idx+i)%len(field_tags)]}:({quote_term(t)})' for i, t in enumerate(terms)]

    # 1. AND combinations (pairs, triples)
    for r in range(2, min(4, len(expanded)+1)):
        for combo in itertools.combinations(expanded, r):
            for terms in itertools.product(*combo):
                tagged = tag_terms(terms)
                q = " AND ".join(tagged)
                queries.add(q)

    # 2. OR within a concept, AND with others
    for i, group in enumerate(expanded):
        if len(group) > 1:
            or_query = "(" + " OR ".join(f'ABST:({quote_term(t)})' for t in group) + ")"
            rest = [expanded[j][0] for j in range(len(expanded)) if j != i]
            if rest:
                tagged_rest = tag_terms(rest, tag_idx=1)
                q = or_query + " AND " + " AND ".join(tagged_rest)
            else:
                q = or_query
            queries.add(q)

    # 3. Single concept ORs (for broad recall)
    for group in expanded:
        if len(group) > 1:
            q = "(" + " OR ".join(f'DESC:({quote_term(t)})' for t in group) + ")"
            queries.add(q)

    # 4. Mix AND/OR for diversity
    if len(expanded) > 2:
        for i in range(len(expanded)):
            for j in range(i+1, len(expanded)):
                or_group = expanded[i] + expanded[j]
                or_query = "(" + " OR ".join(f'TTL:({quote_term(t)})' for t in or_group) + ")"
                rest = [expanded[k][0] for k in range(len(expanded)) if k != i and k != j]
                if rest:
                    tagged_rest = tag_terms(rest, tag_idx=2)
                    q = or_query + " AND " + " AND ".join(tagged_rest)
                else:
                    q = or_query
                queries.add(q)

    # 5. All concepts as a big OR (very broad)
    all_terms = [t for group in expanded for t in group]
    if len(all_terms) > 1:
        queries.add("(" + " OR ".join(f'ABST:({quote_term(t)})' for t in all_terms) + ")")

    # Limit to max_queries
    return list(queries)[:max_queries]


def generate_structured_queries(concepts: List[str], max_queries: int = 10) -> Dict[str, List[str]]:
    """
    Generate a JSON-serializable dict of patent search queries.
    """
    queries = generate_query_variations(concepts, max_queries)
    return {"queries": queries}


if __name__ == "__main__":
    concepts = [
        "autonomous drone navigation",
        "obstacle avoidance",
        "real-time sensor fusion",
        "aerial mapping"
    ]
    result = generate_structured_queries(concepts)
    print(json.dumps(result, indent=2))
