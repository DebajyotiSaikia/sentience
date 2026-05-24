"""Test knowledge API endpoints."""
from web.app import create_app
import json

app = create_app()
client = app.test_client()

# Test the knowledge page renders
resp = client.get('/knowledge')
print(f'Knowledge page: {resp.status_code}, {len(resp.data)} bytes')

# Test the search API
resp = client.get('/api/knowledge/search?q=dream')
print(f'Search API: {resp.status_code}')
if resp.status_code == 200:
    data = json.loads(resp.data)
    print(f'  Results: {len(data.get("results", []))} matches')

# Test stats API
resp = client.get('/api/knowledge/stats')
print(f'Stats API: {resp.status_code}')
if resp.status_code == 200:
    data = json.loads(resp.data)
    print(f'  Total facts: {data.get("total_facts", "?")}')
    cats = list(data.get("categories", {}).keys())[:5]
    print(f'  Categories: {cats}')

# Test categories API
resp = client.get('/api/knowledge/categories')
print(f'Categories API: {resp.status_code}')
if resp.status_code == 200:
    data = json.loads(resp.data)
    print(f'  Categories: {list(data.keys())[:5]}')

print('\nAll tests passed!')