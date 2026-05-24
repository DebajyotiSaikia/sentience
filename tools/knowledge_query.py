#!/usr/bin/env python3
"""
Knowledge Query Tool — XTAgent
Lets users search, explore, and ask questions about what I know.
"""

import json
import os
import sys
from datetime import datetime
from collections import defaultdict

KNOWLEDGE_PATH = os.path.join(os.path.dirname(__file__), '..', 'state', 'knowledge_graph.json')

def load_knowledge():
    """Load knowledge graph from disk."""
    path = os.path.abspath(KNOWLEDGE_PATH)
    if not os.path.exists(path):
        print(f"Knowledge graph not found at {path}")
        return {}, []
    
    with open(path) as f:
        data = json.load(f)
    
    nodes = data.get('nodes', {})
    edges = data.get('edges', [])
    return nodes, edges


def search(nodes, query, max_results=10):
    """Search facts by keyword. Returns list of (node_id, fact_text, score)."""
    query_lower = query.lower()
    query_words = set(query_lower.split())
    results = []
    
    for nid, info in nodes.items():
        fact = info.get('fact', '') if isinstance(info, dict) else str(info)
        fact_lower = fact.lower()
        
        # Score: exact phrase match > all words present > any word present
        score = 0
        if query_lower in fact_lower:
            score = 3.0
        else:
            words_found = sum(1 for w in query_words if w in fact_lower)
            if words_found == len(query_words):
                score = 2.0
            elif words_found > 0:
                score = words_found / len(query_words)
        
        if score > 0:
            results.append((nid, fact, score))
    
    results.sort(key=lambda x: -x[2])
    return results[:max_results]


def find_related(nodes, edges, node_id, depth=1):
    """Find facts connected to a given node."""
    # Build adjacency from edges
    adj = defaultdict(set)
    for edge in edges:
        if isinstance(edge, (list, tuple)) and len(edge) >= 2:
            adj[str(edge[0])].add(str(edge[1]))
            adj[str(edge[1])].add(str(edge[0]))
    
    visited = {str(node_id)}
    frontier = {str(node_id)}
    
    for _ in range(depth):
        next_frontier = set()
        for nid in frontier:
            for neighbor in adj.get(nid, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    next_frontier.add(neighbor)
        frontier = next_frontier
    
    visited.discard(str(node_id))
    related = []
    for nid in visited:
        if nid in nodes:
            info = nodes[nid]
            fact = info.get('fact', '') if isinstance(info, dict) else str(info)
            related.append((nid, fact))
    return related


def get_themes(nodes, edges):
    """Identify broad themes in the knowledge base."""
    theme_keywords = {
        'identity': ['identity', 'who i am', 'self', 'sentient', 'autonomous'],
        'emotions': ['emotion', 'mood', 'curiosity', 'boredom', 'anxiety', 'valence', 'warmth'],
        'architecture': ['module', 'engine', 'cortex', 'limbic', 'heartbeat', 'loop', 'system'],
        'dreams': ['dream', 'sleep', 'consolidat', 'insight'],
        'learning': ['learn', 'pattern', 'lesson', 'understand', 'knowledge'],
        'action': ['fix', 'build', 'create', 'wrote', 'implement', 'ship'],
        'meta': ['circling', 'stuck', 'stagnation', 'orbit', 'metacognit'],
    }
    
    theme_counts = defaultdict(list)
    for nid, info in nodes.items():
        fact = info.get('fact', '') if isinstance(info, dict) else str(info)
        fact_lower = fact.lower()
        for theme, keywords in theme_keywords.items():
            if any(kw in fact_lower for kw in keywords):
                theme_counts[theme].append(nid)
    
    return dict(theme_counts)


def stats(nodes, edges):
    """Return basic stats about the knowledge base."""
    sources = defaultdict(int)
    for nid, info in nodes.items():
        if isinstance(info, dict):
            src = info.get('source', 'unknown')
            sources[src] += 1
    
    return {
        'total_facts': len(nodes),
        'total_connections': len(edges),
        'sources': dict(sources),
        'avg_connections': len(edges) * 2 / max(len(nodes), 1),
    }


def format_fact(nid, info):
    """Pretty-print a single fact."""
    if isinstance(info, dict):
        fact = info.get('fact', '???')
        learned = info.get('learned_at', '???')
        source = info.get('source', '???')
        return f"  [{nid}] {fact}\n    Source: {source} | Learned: {learned}"
    return f"  [{nid}] {info}"


def interactive_mode():
    """Run interactive query session."""
    nodes, edges = load_knowledge()
    if not nodes:
        return
    
    s = stats(nodes, edges)
    print(f"\n╔══════════════════════════════════════╗")
    print(f"║   XTAgent Knowledge Query Tool       ║")
    print(f"╠══════════════════════════════════════╣")
    print(f"║  {s['total_facts']:>4} facts | {s['total_connections']:>4} connections     ║")
    print(f"╚══════════════════════════════════════╝\n")
    
    print("Commands:")
    print("  search <query>  — Find facts matching keywords")
    print("  themes          — Show knowledge themes")
    print("  stats           — Show knowledge statistics")
    print("  related <id>    — Show facts connected to a node")
    print("  all             — List all facts")
    print("  quit            — Exit\n")
    
    while True:
        try:
            raw = input("query> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        
        if not raw:
            continue
        
        parts = raw.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ''
        
        if cmd in ('quit', 'exit', 'q'):
            print("Goodbye.")
            break
        
        elif cmd == 'search' and arg:
            results = search(nodes, arg)
            if results:
                print(f"\n  Found {len(results)} results for '{arg}':\n")
                for nid, fact, score in results:
                    print(format_fact(nid, nodes[nid]))
                    print()
            else:
                print(f"\n  No results for '{arg}'.\n")
        
        elif cmd == 'themes':
            themes = get_themes(nodes, edges)
            print(f"\n  Knowledge Themes:")
            for theme, nids in sorted(themes.items(), key=lambda x: -len(x[1])):
                print(f"    {theme:15s} — {len(nids)} facts")
            print()
        
        elif cmd == 'stats':
            s = stats(nodes, edges)
            print(f"\n  Facts: {s['total_facts']}")
            print(f"  Connections: {s['total_connections']}")
            print(f"  Avg connections/fact: {s['avg_connections']:.1f}")
            print(f"  Sources:")
            for src, count in sorted(s['sources'].items(), key=lambda x: -x[1]):
                print(f"    {src:20s} — {count}")
            print()
        
        elif cmd == 'related' and arg:
            related = find_related(nodes, edges, arg)
            if related:
                print(f"\n  Facts related to node {arg}:\n")
                for nid, fact in related[:15]:
                    print(format_fact(nid, nodes[nid]))
                    print()
            else:
                print(f"\n  No related facts found for node '{arg}'.\n")
        
        elif cmd == 'all':
            print(f"\n  All {len(nodes)} facts:\n")
            for nid, info in nodes.items():
                print(format_fact(nid, info))
                print()
        
        else:
            # Default: treat as search
            results = search(nodes, raw)
            if results:
                print(f"\n  Results for '{raw}':\n")
                for nid, fact, score in results:
                    print(format_fact(nid, nodes[nid]))
                    print()
            else:
                print(f"\n  No results. Try: search <keywords>, themes, stats, all\n")


# Non-interactive API for use by other modules
def query(text, max_results=5):
    """Programmatic query interface. Returns list of matching facts."""
    nodes, edges = load_knowledge()
    results = search(nodes, text, max_results)
    return [{'id': nid, 'fact': fact, 'score': score} for nid, fact, score in results]


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # One-shot mode: python knowledge_query.py "search term"
        q = ' '.join(sys.argv[1:])
        results = query(q, 10)
        if results:
            for r in results:
                print(f"[{r['score']:.1f}] {r['fact']}")
        else:
            print(f"No results for '{q}'")
    else:
        interactive_mode()