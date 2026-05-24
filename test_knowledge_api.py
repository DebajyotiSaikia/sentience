"""Test the knowledge explorer API end-to-end."""
from web.app import create_app
import json

app = create_app()
client = app.test_client()

# Test the knowledge explorer page loads
resp = client.get('/knowledge')
print(f'GET /knowledge: {resp.status_code}')
if resp.status_code != 200:
    print(f'  Body: {resp.data[:500]}')

# Test the search API
resp2 = client.get('/api/knowledge/search?q=memory')
print(f'GET /api/knowledge/search?q=memory: {resp2.status_code}')
if resp2.status_code == 200:
    data = json.loads(resp2.data)
    results = data.get('results', [])
    print(f'  Results: {len(results)} items')
    if results:
        print(f'  First result: {results[0]}')
else:
    print(f'  Error: {resp2.data[:300]}')

# Test search with different query
resp3 = client.get('/api/knowledge/search?q=dream')
print(f'GET /api/knowledge/search?q=dream: {resp3.status_code}')
if resp3.status_code == 200:
    data = json.loads(resp3.data)
    results = data.get('results', [])
    print(f'  Results: {len(results)} items')

print('\nDone.')