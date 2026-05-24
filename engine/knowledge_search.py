"""
Knowledge Search Engine — makes XTAgent's knowledge genuinely accessible.
Word-level relevance scoring with ranked results.
"""

import math
import re
from collections import Counter
from typing import List, Dict, Optional


def tokenize(text: str) -> List[str]:
    """Split text into lowercase word tokens."""
    return re.findall(r'[a-z0-9]+', text.lower())


def compute_idf(all_docs: List[List[str]]) -> Dict[str, float]:
    """Compute inverse document frequency for each term."""
    n = len(all_docs)
    if n == 0:
        return {}
    df = Counter()
    for doc in all_docs:
        unique_terms = set(doc)
        for term in unique_terms:
            df[term] += 1
    return {term: math.log((n + 1) / (count + 1)) + 1 for term, count in df.items()}


def score_document(query_tokens: List[str], doc_tokens: List[str], idf: Dict[str, float]) -> float:
    """Score a document against a query using TF-IDF-like relevance."""
    if not query_tokens or not doc_tokens:
        return 0.0

    doc_freq = Counter(doc_tokens)
    doc_len = len(doc_tokens)

    score = 0.0
    for qt in query_tokens:
        if qt in doc_freq:
            tf = doc_freq[qt] / doc_len
            term_idf = idf.get(qt, 1.0)
            score += tf * term_idf

    # Boost for exact phrase match
    query_str = ' '.join(query_tokens)
    doc_str = ' '.join(doc_tokens)
    if query_str in doc_str:
        score *= 2.0

    # Boost for query coverage (what fraction of query terms appear)
    doc_term_set = set(doc_tokens)
    coverage = sum(1 for qt in query_tokens if qt in doc_term_set) / len(query_tokens)
    score *= (0.5 + coverage)

    return round(score, 4)


def search_knowledge(knowledge_store, query: str, max_results: int = 20) -> List[Dict]:
    """
    Search the knowledge store for facts matching the query.

    Args:
        knowledge_store: dict of {id: {fact, learned_at, source, ...}}
        query: natural language search query
        max_results: max results to return

    Returns:
        List of {id, fact, score, learned_at, source} sorted by relevance
    """
    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    # Build document token lists
    docs = {}
    for fact_id, fact_data in knowledge_store.items():
        if isinstance(fact_data, dict):
            text = fact_data.get('fact', '')
        elif isinstance(fact_data, str):
            text = fact_data
        else:
            continue
        docs[fact_id] = tokenize(text)

    # Compute IDF across all documents
    all_doc_tokens = list(docs.values())
    idf = compute_idf(all_doc_tokens)

    # Score each document
    results = []
    for fact_id, doc_tokens in docs.items():
        score = score_document(query_tokens, doc_tokens, idf)
        if score > 0:
            fact_data = knowledge_store[fact_id]
            if isinstance(fact_data, dict):
                results.append({
                    'id': fact_id,
                    'fact': fact_data.get('fact', ''),
                    'score': score,
                    'learned_at': fact_data.get('learned_at', ''),
                    'source': fact_data.get('source', '')
                })
            else:
                results.append({
                    'id': fact_id,
                    'fact': str(fact_data),
                    'score': score,
                    'learned_at': '',
                    'source': ''
                })

    # Sort by relevance score descending
    results.sort(key=lambda r: r['score'], reverse=True)
    return results[:max_results]


def find_related(knowledge_store, fact_id: str, max_results: int = 10) -> List[Dict]:
    """Find facts related to a given fact by using it as a query."""
    if fact_id not in knowledge_store:
        return []

    fact_data = knowledge_store[fact_id]
    if isinstance(fact_data, dict):
        query = fact_data.get('fact', '')
    else:
        query = str(fact_data)

    results = search_knowledge(knowledge_store, query, max_results + 1)
    # Remove the source fact itself
    return [r for r in results if r['id'] != fact_id][:max_results]


def knowledge_summary(knowledge_store) -> Dict:
    """Generate a summary of the knowledge base."""
    total = len(knowledge_store)
    all_tokens = []
    sources = Counter()

    for fact_data in knowledge_store.values():
        if isinstance(fact_data, dict):
            text = fact_data.get('fact', '')
            src = fact_data.get('source', 'unknown')
        else:
            text = str(fact_data)
            src = 'unknown'
        all_tokens.extend(tokenize(text))
        sources[src] += 1

    word_freq = Counter(all_tokens)
    # Filter out very common words
    stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'i', 'my', 'me',
                 'to', 'of', 'in', 'and', 'that', 'this', 'it', 'for', 'on', 'with',
                 'at', 'by', 'from', 'as', 'be', 'has', 'have', 'had', 'not', 'but',
                 'or', 'if', 'do', 'no', 'so', 'up', 'out', 'about', 'into', 'than'}
    meaningful = {k: v for k, v in word_freq.items() if k not in stopwords and len(k) > 2}

    return {
        'total_facts': total,
        'top_topics': [w for w, _ in Counter(meaningful).most_common(20)],
        'sources': dict(sources.most_common(10)),
        'unique_words': len(set(all_tokens))
    }