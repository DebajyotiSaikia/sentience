import json

with open('data/knowledge_graph.json', 'r') as f:
    db = json.load(f)

nodes = db.get('nodes', {})
dreams = [n for n in nodes.values() if n.get('category') == 'dream']
print(f'Found {len(dreams)} dream nodes')
print()

for d in sorted(dreams, key=lambda x: x.get('created', ''))[:20]:
    print('---')
    content = d.get('content', '')[:300]
    print(content)
    print()