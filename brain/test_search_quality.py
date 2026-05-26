"""Test the knowledge search from a user's perspective — is it actually useful?"""
from web.app import create_app
import json

app = create_app()
client = app.test_client()

queries = ['consciousness', 'emotion', 'dream', 'identity', 'memory', 'xyznonexistent']

for q in queries:
    r = client.get(f'/api/knowledge/search?q={q}')
    print(f'\nSearch "{q}": status={r.status_code}')
    if r.status_code == 200:
        data = json.loads(r.data)
        results = data.get('results', data.get('facts', []))
        print(f'  Results: {len(results)}')
        for item in results[:3]:
            if isinstance(item, dict):
                text = item.get('fact', item.get('text', str(item)))[:100]
                score = item.get('score', item.get('relevance', '?'))
                print(f'  [{score}] {text}')
            else:
                print(f'  - {str(item)[:100]}')
    else:
        print(f'  Error: {r.data.decode()[:200]}')

# Also test the knowledge page itself renders search results
r2 = client.get('/knowledge?q=consciousness')
print(f'\n/knowledge?q=consciousness: status={r2.status_code}, size={len(r2.data)} bytes')
has_results = b'consciousness' in r2.data.lower()
print(f'  Contains "consciousness": {has_results}')