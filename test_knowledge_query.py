"""Test what exists, what works, what doesn't. Run ONCE then build."""
import sys, json, os
from collections import Counter
sys.path.insert(0, '.')

# 1. Knowledge graph shape
kg = json.load(open('brain/knowledge.json'))
nodes = kg.get('nodes', {})
edges = kg.get('edges', [])
print(f"=== Knowledge Graph: {len(nodes)} nodes, {len(edges)} edges ===")

# 2. Simple search
query = "curiosity"
matches = []
for nid, node in nodes.items():
    fact = node.get('fact', '') if isinstance(node, dict) else str(node)
    if query.lower() in fact.lower():
        matches.append((nid, fact[:100]))
print(f"\nSearch '{query}': {len(matches)} hits")
for nid, m in matches[:3]:
    print(f"  [{nid}] {m}")

# 3. Edge analysis
print(f"\nEdge format sample: {edges[0] if edges else 'none'}")
conn = Counter()
for e in edges:
    if isinstance(e, (list, tuple)) and len(e) >= 2:
        conn[e[0]] += 1
        conn[e[1]] += 1
    elif isinstance(e, dict):
        conn[e.get('source', '?')] += 1
        conn[e.get('target', '?')] += 1
print(f"Top connected nodes:")
for nid, count in conn.most_common(5):
    node = nodes.get(nid, {})
    fact = node.get('fact', '?')[:60] if isinstance(node, dict) else str(node)[:60]
    print(f"  [{nid}] ({count} edges) {fact}")

# 4. Check what web routes exist
try:
    from web.app import create_app
    app = create_app()
    routes = []
    for r in app.url_map.iter_rules():
        if not r.rule.startswith('/static'):
            methods = list(r.methods - {'HEAD', 'OPTIONS'})
            routes.append((r.rule, methods))
    routes.sort()
    print(f"\n=== Web Routes: {len(routes)} total ===")
    for rule, methods in routes:
        print(f"  {','.join(methods):6s} {rule}")
except Exception as e:
    print(f"\nWeb app error: {e}")

print("\n=== DONE ===")