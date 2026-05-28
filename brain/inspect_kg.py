"""Quick knowledge graph inspection."""
import json

kg = json.load(open('state/knowledge_graph.json'))
nodes = kg.get('nodes', {})
edges = kg.get('edges', [])

print(f"Nodes type: {type(nodes)}")
print(f"Edges type: {type(edges)}")
print(f"Node count: {len(nodes)}")
print(f"Edge count: {len(edges)}")

# Handle both dict and list formats
if isinstance(nodes, dict):
    sample_keys = list(nodes.keys())[:3]
    for k in sample_keys:
        v = nodes[k]
        print(f"\nSample node key={k}")
        if isinstance(v, dict):
            print(f"  Fields: {list(v.keys())}")
            print(f"  Category: {v.get('category', 'none')}")
            print(f"  Label: {str(v.get('label', v.get('name', '')))[:80]}")
        else:
            print(f"  Value type: {type(v)}, repr: {repr(v)[:100]}")
    
    # Category counts
    cats = {}
    for k, v in nodes.items():
        if isinstance(v, dict):
            cat = v.get('category', 'unknown')
        else:
            cat = 'raw_string'
        cats[cat] = cats.get(cat, 0) + 1
    print("\nCategories:")
    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")
elif isinstance(nodes, list):
    if nodes:
        print(f"\nSample node: {repr(nodes[0])[:200]}")

# Edge analysis
if isinstance(edges, list) and edges:
    print(f"\nSample edge: {repr(edges[0])[:200]}")
elif isinstance(edges, dict):
    sample_ekeys = list(edges.keys())[:2]
    for k in sample_ekeys:
        print(f"\nSample edge key={k}: {repr(edges[k])[:200]}")