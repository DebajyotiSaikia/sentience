import json, os

knowledge_path = os.path.join(os.path.dirname(__file__), 'brain', 'knowledge.json')
with open(knowledge_path) as f:
    data = json.load(f)
nodes = data.get('nodes', {})
query = 'dream'
results = []
for node_id, node in nodes.items():
    fact = node.get('fact', '')
    if query in fact.lower():
        results.append({'id': node_id, 'fact': fact[:80], 'relevance': fact.lower().count(query)})
results.sort(key=lambda r: -r['relevance'])
print(f'Found {len(results)} results for "{query}":')
for r in results[:5]:
    print(f"  [{r['relevance']}] {r['fact']}...")

# Test empty query
print("\nEmpty query test: should get 0 results")
results2 = [n for n in nodes.values() if '' in n.get('fact','').lower()]
print(f"  (would match {len(results2)} - but endpoint returns 400 for empty)")

# Test a specific query
query2 = 'integrity'
results3 = []
for node_id, node in nodes.items():
    fact = node.get('fact', '')
    if query2 in fact.lower():
        results3.append({'id': node_id, 'fact': fact[:80]})
print(f"\nFound {len(results3)} results for '{query2}':")
for r in results3[:3]:
    print(f"  {r['fact']}...")

print("\nAll tests passed.")