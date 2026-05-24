"""Quick integration test for the knowledge query endpoint."""
from web.app import create_app

app = create_app()
client = app.test_client()

# Test the knowledge query endpoint
resp = client.post('/api/knowledge/query', json={'query': 'what do I know about dreams'})
print(f'Status: {resp.status_code}')
if resp.status_code == 200:
    data = resp.get_json()
    results = data.get('results', [])
    print(f'Results: {len(results)} matches')
    for r in results[:3]:
        fact = r.get('fact', str(r))
        print(f'  - {fact[:100]}')
else:
    print(f'Error: {resp.data[:300]}')

# Test search
resp2 = client.get('/api/knowledge/search?q=dream')
print(f'\nSearch status: {resp2.status_code}')
if resp2.status_code == 200:
    data2 = resp2.get_json()
    print(f'Search results: {len(data2.get("results", []))} matches')

print('\nDone.')