import json, os

graph_path = os.path.join('state', 'knowledge_graph.json')
with open(graph_path) as f:
    data = json.load(f)

nodes = data.get('nodes', {})
print(f'Graph has {len(nodes)} nodes')

# Simulate a search for 'dream'
query = 'dream'
results = []
for nid, info in nodes.items():
    fact = info.get('fact', '') if isinstance(info, dict) else str(info)
    if query.lower() in fact.lower():
        results.append({'id': nid, 'fact': fact[:100]})

print(f'Search for "{query}" found {len(results)} results')
for r in results[:5]:
    print(f'  - [{r["id"]}] {r["fact"]}')

# Check what routes exist in app.py
print('\n--- Existing knowledge routes in web/app.py ---')
with open('web/app.py') as f:
    for i, line in enumerate(f, 1):
        if 'knowledge' in line.lower() or 'search' in line.lower():
            print(f'  L{i}: {line.rstrip()}')