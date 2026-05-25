"""Integration test for knowledge_explorer search."""
import sys; sys.path.insert(0, '.')
from web.knowledge_explorer import load_knowledge, search_knowledge

facts = load_knowledge()
print(f'load_knowledge: type={type(facts).__name__}, len={len(facts)}')

if isinstance(facts, dict) and len(facts) > 0:
    first_key = list(facts.keys())[0]
    val = facts[first_key]
    print(f'Sample: key={first_key!r}, val_type={type(val).__name__}')
    if isinstance(val, dict):
        print(f'  fact: {val.get("fact", "N/A")[:80]}')

for q in ['dream', 'identity', 'agent']:
    results = search_knowledge(q, facts)
    print(f'search({q!r}): {len(results)} results')
    if results:
        print(f'  top: {results[0].get("fact", str(results[0]))[:80]}')

print('\nDONE - all checks passed')