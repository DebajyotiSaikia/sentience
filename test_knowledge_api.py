import sys
sys.path.insert(0, '.')

from core.knowledge_graph import KnowledgeGraph

kg = KnowledgeGraph()
facts = kg.facts if hasattr(kg, 'facts') else {}
print(f'Knowledge graph has {len(facts)} facts')

# Check available methods
methods = [m for m in dir(kg) if not m.startswith('_')]
print(f'Available methods: {methods}')

# Test search if it exists
if hasattr(kg, 'search'):
    results = kg.search('dream')
    print(f'Search for "dream": {len(results)} results')
    if results:
        print(f'  First: {str(results[0])[:150]}')
elif hasattr(kg, 'query'):
    results = kg.query('dream')
    print(f'Query for "dream": {len(results)} results')
else:
    # Try manual search through facts
    matches = []
    for fid, fdata in facts.items():
        text = fdata if isinstance(fdata, str) else fdata.get('fact', str(fdata))
        if 'dream' in text.lower():
            matches.append(text)
    print(f'Manual search for "dream": {len(matches)} matches')
    if matches:
        print(f'  First: {matches[0][:150]}')

# Show a sample of facts
print('\n--- Sample facts ---')
count = 0
for fid, fdata in list(facts.items())[:5]:
    text = fdata if isinstance(fdata, str) else fdata.get('fact', str(fdata))
    print(f'  [{fid}] {text[:100]}')
    count += 1
print(f'  ... ({len(facts) - count} more)')