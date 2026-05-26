"""Diagnose search relevance — why are 'emotion', 'identity', 'dream' returning bad results?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

for q in ['emotion', 'identity', 'dream']:
    resp = client.get(f'/api/search?q={q}')
    print(f'\n=== Search "{q}" === status={resp.status_code}')
    if resp.status_code == 200:
        data = resp.get_json()
        results = data.get('results', [])
        print(f'  {len(results)} results')
        for r in results[:3]:
            content = r.get('content', r.get('fact', ''))[:120]
            score = r.get('score', r.get('relevance', '?'))
            print(f'  [{score}] {content}')
    else:
        print(f'  Error: {resp.data[:200]}')

# Also check what knowledge data exists
print("\n=== Knowledge Data Check ===")
import json
for path in ['brain/knowledge.json', 'persist/knowledge_graph.json']:
    full = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), path)
    if os.path.exists(full):
        with open(full) as f:
            data = json.load(f)
        if isinstance(data, dict):
            nodes = data.get('nodes', data)
            print(f'{path}: {len(nodes)} nodes (dict)')
            # Show a sample
            for k, v in list(nodes.items())[:3]:
                fact = v.get('fact', str(v))[:100] if isinstance(v, dict) else str(v)[:100]
                print(f'  [{k}] {fact}')
        elif isinstance(data, list):
            print(f'{path}: {len(data)} items (list)')
    else:
        print(f'{path}: NOT FOUND')

# Check what the UX audit considers "relevant"
print("\n=== Relevance Check ===")
print("For 'emotion' query, relevant results should contain 'emotion' or related words")
print("For 'identity' query, relevant results should contain 'identity', 'who', 'am' etc")