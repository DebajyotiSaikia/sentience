import sys; sys.path.insert(0, '.')
from web.knowledge_api import _load_knowledge

# Test search functionality
data = _load_knowledge()
query = 'dream'
results = []
for kid, kdata in data.items():
    fact = kdata.get('fact', '') if isinstance(kdata, dict) else str(kdata)
    if query.lower() in fact.lower() or query.lower() in kid.lower():
        results.append({'id': kid, 'fact': fact[:80]})
print(f'Search for "dream": {len(results)} results')
for r in results[:5]:
    print(f'  - [{r["id"]}] {r["fact"]}')

# Test stats
print(f'\nTotal facts: {len(data)}')
sources = {}
for kid, kdata in data.items():
    src = kdata.get('source', 'unknown') if isinstance(kdata, dict) else 'unknown'
    sources[src] = sources.get(src, 0) + 1
print(f'Sources: {sources}')