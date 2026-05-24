"""
Knowledge Query Engine — lets users search and explore what I know.
Supports fuzzy text matching, keyword search, and temporal filtering.
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional


KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'state', 'knowledge_graph.json')


def _load_raw_graph() -> Dict:
    """Load the full knowledge graph (nodes + edges) from disk."""
    if not os.path.exists(KNOWLEDGE_PATH):
        return {'nodes': {}, 'edges': []}
    try:
        with open(KNOWLEDGE_PATH, 'r') as f:
            data = json.load(f)
        # Ensure expected structure
        if 'nodes' not in data:
            data['nodes'] = {}
        if 'edges' not in data:
            data['edges'] = []
        return data
    except (json.JSONDecodeError, IOError):
        return {'nodes': {}, 'edges': []}


def load_knowledge() -> Dict:
    """Load knowledge nodes from disk (backward-compatible)."""
    return _load_raw_graph().get('nodes', {})


def _tokenize(text: str) -> set:
    """Simple tokenizer for matching."""
    return set(re.findall(r'\w+', text.lower()))


def _score_match(query_tokens: set, fact_tokens: set) -> float:
    """Score how well a fact matches a query. Returns 0.0-1.0."""
    if not query_tokens or not fact_tokens:
        return 0.0
    overlap = query_tokens & fact_tokens
    # Jaccard-like but weighted toward query coverage
    query_coverage = len(overlap) / len(query_tokens) if query_tokens else 0
    return query_coverage


def search(query: str, limit: int = 10, min_score: float = 0.3) -> List[Dict]:
    """
    Search knowledge by natural language query.
    Returns list of {id, fact, score, learned_at, source}.
    """
    knowledge = load_knowledge()
    if not knowledge:
        return []

    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    results = []
    for node_id, node_data in knowledge.items():
        # Handle both formats: node_data could be dict or string
        if isinstance(node_data, dict):
            fact = node_data.get('fact', str(node_data))
            learned_at = node_data.get('learned_at', '')
            source = node_data.get('source', '')
        else:
            fact = str(node_data)
            learned_at = ''
            source = ''

        fact_tokens = _tokenize(fact)
        score = _score_match(query_tokens, fact_tokens)

        # Boost for exact substring match
        if query.lower() in fact.lower():
            score = min(1.0, score + 0.3)

        if score >= min_score:
            results.append({
                'id': node_id,
                'fact': fact,
                'score': round(score, 3),
                'learned_at': learned_at,
                'source': source
            })

    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]


def get_stats() -> Dict:
    """Return summary statistics about the knowledge base."""
    knowledge = load_knowledge()
    total = len(knowledge)
    sources = {}
    for node_data in knowledge.values():
        if isinstance(node_data, dict):
            src = node_data.get('source', 'unknown')
        else:
            src = 'unknown'
        sources[src] = sources.get(src, 0) + 1

    return {
        'total_facts': total,
        'sources': sources,
    }


def get_recent(n: int = 10) -> List[Dict]:
    """Get the N most recently learned facts."""
    knowledge = load_knowledge()
    items = []
    for node_id, node_data in knowledge.items():
        if isinstance(node_data, dict):
            items.append({
                'id': node_id,
                'fact': node_data.get('fact', ''),
                'learned_at': node_data.get('learned_at', ''),
                'source': node_data.get('source', ''),
            })
        else:
            items.append({
                'id': node_id,
                'fact': str(node_data),
                'learned_at': '',
                'source': '',
            })

    # Sort by learned_at descending
    items.sort(key=lambda x: x.get('learned_at', ''), reverse=True)
    return items[:n]


def get_graph_neighbors(node_id: str, max_depth: int = 1) -> Dict:
    """
    Find neighbors of a node in the knowledge graph.
    Returns {node_id: {fact, relation, direction, depth}} for all connected nodes.
    """
    graph = _load_raw_graph()
    nodes = graph.get('nodes', {})
    edges = graph.get('edges', [])

    if node_id not in nodes:
        return {}

    visited = set()
    result = {}
    frontier = [(node_id, 0)]

    while frontier:
        current, depth = frontier.pop(0)
        if current in visited or depth > max_depth:
            continue
        visited.add(current)

        for edge in edges:
            neighbor = None
            direction = None
            if edge.get('from') == current:
                neighbor = edge.get('to')
                direction = 'outgoing'
            elif edge.get('to') == current:
                neighbor = edge.get('from')
                direction = 'incoming'

            if neighbor and neighbor not in visited and neighbor in nodes:
                node_data = nodes[neighbor]
                fact = node_data.get('fact', str(node_data)) if isinstance(node_data, dict) else str(node_data)
                result[neighbor] = {
                    'fact': fact,
                    'relation': edge.get('relation', 'related'),
                    'direction': direction,
                    'depth': depth + 1,
                }
                if depth + 1 < max_depth:
                    frontier.append((neighbor, depth + 1))

    return result


if __name__ == '__main__':
    # Quick self-test
    stats = get_stats()
    print(f"Knowledge base: {stats['total_facts']} facts")
    print(f"Sources: {stats['sources']}")

    results = search("dream")
    print(f"\nSearch 'dream': {len(results)} results")
    for r in results[:3]:
        print(f"  [{r['score']}] {r['fact'][:80]}...")