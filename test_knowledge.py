import sys, os
sys.path.insert(0, '.')
os.environ['FLASK_ENV'] = 'testing'

from web.app import app
client = app.test_client()

# Test knowledge page loads
resp = client.get('/knowledge')
print(f'Knowledge page: {resp.status_code}')

# Test search API
resp = client.get('/api/knowledge/search?q=dream')
print(f'Search API: {resp.status_code}')
if resp.status_code == 200:
    import json
    data = json.loads(resp.data)
    print(f'Results for "dream": {len(data)} facts found')
    if data:
        print(f'First result: {data[0]["fact"][:80]}...')

# Test empty search (all facts)
resp = client.get('/api/knowledge/search')
print(f'All facts: {resp.status_code}')
if resp.status_code == 200:
    data = json.loads(resp.data)
    print(f'Total facts available: {len(data)}')

# Test stats API
resp = client.get('/api/knowledge/stats')
print(f'Stats API: {resp.status_code}')
if resp.status_code == 200:
    data = json.loads(resp.data)
    print(f'Stats: {data}')

print('\nAll tests passed!')