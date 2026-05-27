"""Diagnose why knowledge search misses known facts."""
import json, os

paths = [
    'data/knowledge_graph.json',
    os.path.expanduser('~/data/knowledge_graph.json'),
    'data/knowledge/knowledge_graph.json',
]

for p in paths:
    if os.path.exists(p):
        with open(p) as f:
            d = json.load(f)
        print(f"Found: {p}")
        if isinstance(d, dict):
            nodes = d.get('nodes', [])
            print(f"Nodes: {len(nodes)}")
            if nodes and isinstance(nodes[0], dict):
                print(f"Node keys: {list(nodes[0].keys())}")
                # Show first 3 nodes
                for n in nodes[:3]:
                    print(f"  Sample: {json.dumps(n)[:150]}")
                # Search for consciousness
                matches = [n for n in nodes if isinstance(n, dict) 
                          and 'conscious' in json.dumps(n).lower()]
                print(f"\nNodes mentioning 'conscious': {len(matches)}")
                for m in matches[:5]:
                    print(f"  Match: {json.dumps(m)[:200]}")
        break
else:
    print("No knowledge graph found at any path")
    # Check what's in data/
    for root in ['data', os.path.expanduser('~/data')]:
        if os.path.isdir(root):
            print(f"\nContents of {root}/:")
            for f in os.listdir(root):
                print(f"  {f}")