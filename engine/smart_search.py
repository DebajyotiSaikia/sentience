"""
Smart search over XTAgent's knowledge graph.
Relevance-ranked, multi-word, with related fact suggestions.
"""

import math
import re
from collections import Counter
from typing import List, Dict, Tuple


def tokenize(text: str) -> List[str]:
    """Split text into lowercase tokens, stripping punctuation."""
    return re.findall(r'[a-z0-9]+', text.lower())


def build_idf(facts: List[Dict]) -> Dict[str, float]:
    """Compute inverse document frequency for all terms across facts."""
    n = len(facts)
    if n == 0:
        return {}
    doc_freq = Counter()
    for f in facts:
        tokens = set(tokenize(f.get('fact', '')))
        for t in tokens:
            doc_freq[t] += 1
    return {term: math.log(n / df) for term, df in doc_freq.items()}


def score_fact(query_tokens: List[str], fact_text: str, idf: Dict[str, float]) -> float:
    """Score a single fact against query tokens using TF-IDF-like relevance."""
    fact_tokens = tokenize(fact_text)
    if not fact_tokens or not query_tokens:
        return 0.0

    fact_counts = Counter(fact_tokens)
    fact_len = len(fact_tokens)
    score = 0.0

    for qt in query_tokens:
        if qt in fact_counts:
            tf = fact_counts[qt] / fact_len
            weight = idf.get(qt, 1.0)
            score += tf * weight

    # Bonus for exact phrase match
    fact_lower = fact_text.lower()
    query_str = ' '.join(query_tokens)
    if query_str in fact_lower:
        score *= 1.5

    # Bonus for multiple query terms matching
    matched = sum(1 for qt in query_tokens if qt in fact_counts)
    if len(query_tokens) > 1 and matched > 1:
        coverage = matched / len(query_tokens)
        score *= (1.0 + coverage)

    return score


def search(facts: List[Dict], query: str, top_k: int = 20) -> List[Dict]:
    """
    Search facts by relevance to query.
    Returns top_k results sorted by score, each with added 'score' field.
    """
    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    idf = build_idf(facts)
    scored = []

    for f in facts:
        fact_text = f.get('fact', '')
        s = score_fact(query_tokens, fact_text, idf)
        if s > 0:
            result = dict(f)
            result['score'] = round(s, 4)
            scored.append(result)

    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored[:top_k]


def find_related(facts: List[Dict], anchor_fact: str, exclude_self: bool = True, top_k: int = 5) -> List[Dict]:
    """Find facts related to a given fact by shared vocabulary."""
    anchor_tokens = tokenize(anchor_fact)
    if not anchor_tokens:
        return []

    idf = build_idf(facts)
    scored = []

    for f in facts:
        fact_text = f.get('fact', '')
        if exclude_self and fact_text == anchor_fact:
            continue
        s = score_fact(anchor_tokens, fact_text, idf)
        if s > 0:
            result = dict(f)
            result['score'] = round(s, 4)
            scored.append(result)

    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored[:top_k]


def suggest_queries(facts: List[Dict], top_k: int = 8) -> List[str]:
    """Suggest interesting search queries based on distinctive terms in the knowledge base."""
    idf = build_idf(facts)
    # Find terms that are distinctive (high IDF) but appear in multiple docs
    doc_freq = Counter()
    for f in facts:
        for t in set(tokenize(f.get('fact', ''))):
            doc_freq[t] += 1

    # Filter: must appear in 2+ facts, not too common, not too short
    candidates = []
    n = len(facts)
    for term, df in doc_freq.items():
        if len(term) < 4:
            continue
        if df < 2 or df > n * 0.3:
            continue
        candidates.append((term, idf.get(term, 0) * df))

    candidates.sort(key=lambda x: x[1], reverse=True)
    return [c[0] for c in candidates[:top_k]]