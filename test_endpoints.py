"""Quick test of the new /api/categories and /api/recent endpoints."""
from web.app import create_app

app = create_app()
client = app.test_client()

# Test /api/categories
r = client.get('/api/categories')
print(f'/api/categories: {r.status_code}')
if r.status_code == 200:
    data = r.get_json()
    print(f'  categories: {len(data.get("categories", {}))} types, {data.get("total", 0)} total')

# Test /api/recent
r = client.get('/api/recent?limit=3')
print(f'/api/recent: {r.status_code}')
if r.status_code == 200:
    data = r.get_json()
    print(f'  items: {len(data.get("items", []))} returned, {data.get("total", 0)} total')
    for item in data.get('items', [])[:2]:
        print(f'    - {item["fact"][:80]}')

# Test existing endpoints still work
r = client.get('/api/search?q=dream')
print(f'/api/search?q=dream: {r.status_code}')
r = client.get('/api/search/stats')
print(f'/api/search/stats: {r.status_code}')

# Test chat endpoint
r = client.get('/chat')
print(f'/chat: {r.status_code}')

# Test explore endpoint
r = client.get('/explore')
print(f'/explore: {r.status_code}')

print('\nAll endpoint tests complete!')