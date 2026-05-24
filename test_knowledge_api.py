import json

# Test knowledge graph structure
facts = json.load(open('/workspace/state/knowledge_graph.json'))
print(f'Type: {type(facts).__name__}, Count: {len(facts)}')

# Show one sample fact
if isinstance(facts, dict):
    fid = list(facts.keys())[0]
    print(f'Sample ID: {fid[:20]}...')
    print(f'Sample data: {facts[fid]}')
elif isinstance(facts, list):
    print(f'Sample: {facts[0]}')

# Simulate a search
query = 'dream'
matches = 0
if isinstance(facts, dict):
    for fid, fdata in facts.items():
        text = fdata.get('fact', str(fdata)) if isinstance(fdata, dict) else str(fdata)
        if query in text.lower():
            matches += 1
print(f'Search for "{query}": {matches} matches')