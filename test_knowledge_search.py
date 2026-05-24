import json

data = json.load(open('brain/knowledge.json'))
nodes = data.get('nodes', {})
print(f'Top-level keys: {list(data.keys())}')
print(f'Total nodes: {len(nodes)}')

# Show structure of first few nodes
for i, (k, v) in enumerate(list(nodes.items())[:3]):
    print(f'  Node {k}: {str(v)[:150]}')

# Count facts
total_with_fact = sum(1 for v in nodes.values() if isinstance(v, dict) and 'fact' in v)
print(f'Nodes with "fact" key: {total_with_fact}')

# Search for autonomy
matches = []
for k, v in nodes.items():
    if isinstance(v, dict) and 'fact' in v:
        if 'autonomy' in v['fact'].lower():
            matches.append(f'{k}: {v["fact"][:80]}')
    elif isinstance(v, str) and 'autonomy' in v.lower():
        matches.append(f'{k}: {v[:80]}')

print(f'\nAutonomy matches: {len(matches)}')
for m in matches[:5]:
    print(f'  {m}')

# Now test what the search function does
from web.knowledge_query import search_facts
results = search_facts('autonomy')
print(f'\nsearch_facts("autonomy") returned: {len(results)} results')
if results:
    print(f'  First: {str(results[0])[:120]}')