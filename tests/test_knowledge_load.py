"""Quick test: verify knowledge_explorer can load from brain/knowledge.json"""
import json, os

path = os.path.join('brain', 'knowledge.json')
if os.path.exists(path):
    with open(path) as f:
        data = json.load(f)
    print(f'Type: {type(data).__name__}, Keys: {len(data)}')
    # Show first 3 entries to confirm format
    for i, (k, v) in enumerate(list(data.items())[:3]):
        print(f'  {k}: {type(v).__name__} -> {str(v)[:120]}')
    
    # Test the search logic from knowledge_explorer
    query = 'dream'
    results = []
    for kid, info in data.items():
        if isinstance(info, dict):
            fact = info.get('fact', '')
            if query.lower() in fact.lower():
                results.append({'id': kid, 'fact': fact[:80]})
    print(f'\nSearch for "dream": {len(results)} hits')
    for r in results[:3]:
        print(f'  [{r["id"]}] {r["fact"]}')
else:
    print('NOT FOUND at', path)