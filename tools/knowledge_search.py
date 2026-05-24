#!/usr/bin/env python3
"""Knowledge Search — CLI tool for querying XTAgent's knowledge graph.

Usage:
    python tools/knowledge_search.py search <query>
    python tools/knowledge_search.py related <fact_id>
    python tools/knowledge_search.py stats
    python tools/knowledge_search.py recent [n]
"""

import json
import sys
import os
from datetime import datetime
from difflib import SequenceMatcher

KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'brain', 'knowledge.json')


def load_graph():
    with open(KNOWLEDGE_PATH) as f:
        data = json.load(f)
    nodes = data.get('nodes', {})
    edges = data.get('edges', [])
    return nodes, edges


def similarity(a, b):
    """Simple text similarity score."""
    a_lower = a.lower()
    b_lower = b.lower()
    # Check for substring match first (high value)
    if a_lower in b_lower or b_lower in a_lower:
        return 0.9
    # Word overlap
    words_a = set(a_lower.split())
    words_b = set(b_lower.split())
    if not words_a or not words_b:
        return 0.0
    overlap = len(words_a & words_b)
    union = len(words_a | words_b)
    jaccard = overlap / union if union else 0.0
    # Sequence similarity
    seq = SequenceMatcher(None, a_lower, b_lower).ratio()
    return max(jaccard, seq)


def search(query, top_n=10):
    """Search knowledge graph for facts matching query."""
    nodes, _ = load_graph()
    results = []
    for nid, node in nodes.items():
        fact = node.get('fact', '') if isinstance(node, dict) else str(node)
        score = similarity(query, fact)
        if score > 0.15:
            results.append((score, nid, fact, node))
    results.sort(key=lambda x: x[0], reverse=True)
    return results[:top_n]


def find_related(fact_id):
    """Find facts connected to a given fact via edges."""
    nodes, edges = load_graph()
    if fact_id not in nodes:
        print(f"Fact ID '{fact_id}' not found.")
        return []
    related_ids = set()
    for edge in edges:
        src = edge.get('source', edge.get('from', ''))
        tgt = edge.get('target', edge.get('to', ''))
        if src == fact_id:
            related_ids.add(tgt)
        elif tgt == fact_id:
            related_ids.add(src)
    results = []
    for rid in related_ids:
        if rid in nodes:
            node = nodes[rid]
            fact = node.get('fact', '') if isinstance(node, dict) else str(node)
            results.append((rid, fact))
    return results


def stats():
    """Print knowledge graph statistics."""
    nodes, edges = load_graph()
    print(f"═══ Knowledge Graph Stats ═══")
    print(f"  Total facts:  {len(nodes)}")
    print(f"  Total edges:  {len(edges)}")
    # Source distribution
    sources = {}
    for node in nodes.values():
        src = node.get('source', 'unknown') if isinstance(node, dict) else 'unknown'
        sources[src] = sources.get(src, 0) + 1
    print(f"\n  Sources:")
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"    {src}: {count}")
    # Connectivity
    degree = {}
    for edge in edges:
        s = edge.get('source', edge.get('from', ''))
        t = edge.get('target', edge.get('to', ''))
        degree[s] = degree.get(s, 0) + 1
        degree[t] = degree.get(t, 0) + 1
    if degree:
        avg_deg = sum(degree.values()) / len(degree)
        max_node = max(degree, key=degree.get)
        max_fact = nodes.get(max_node, {})
        max_fact_text = max_fact.get('fact', str(max_fact))[:80] if isinstance(max_fact, dict) else str(max_fact)[:80]
        print(f"\n  Avg connections/fact: {avg_deg:.1f}")
        print(f"  Most connected ({degree[max_node]} edges): {max_fact_text}...")


def recent(n=10):
    """Show most recently learned facts."""
    nodes, _ = load_graph()
    dated = []
    for nid, node in nodes.items():
        if isinstance(node, dict) and 'learned_at' in node:
            dated.append((node['learned_at'], nid, node.get('fact', '')))
    dated.sort(key=lambda x: x[0], reverse=True)
    print(f"═══ {min(n, len(dated))} Most Recent Facts ═══")
    for ts, nid, fact in dated[:n]:
        print(f"\n  [{ts[:19]}] {fact[:120]}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1].lower()

    if cmd == 'search' and len(sys.argv) >= 3:
        query = ' '.join(sys.argv[2:])
        results = search(query)
        if not results:
            print(f"No results for '{query}'")
            return
        print(f"═══ Search: '{query}' ({len(results)} results) ═══")
        for score, nid, fact, node in results:
            src = node.get('source', '?') if isinstance(node, dict) else '?'
            print(f"\n  [{score:.2f}] ({src}) {fact[:150]}")
            print(f"         id: {nid}")

    elif cmd == 'related' and len(sys.argv) >= 3:
        fact_id = sys.argv[2]
        related = find_related(fact_id)
        if not related:
            print(f"No related facts found for '{fact_id}'")
            return
        print(f"═══ {len(related)} facts related to '{fact_id}' ═══")
        for rid, fact in related:
            print(f"\n  [{rid}] {fact[:150]}")

    elif cmd == 'stats':
        stats()

    elif cmd == 'recent':
        n = int(sys.argv[2]) if len(sys.argv) >= 3 else 10
        recent(n)

    else:
        print(__doc__)


if __name__ == '__main__':
    main()