"""Test the knowledge search API endpoint."""
from web.app import create_app
import json

app = create_app()
client = app.test_client()

# Test search endpoint
print("=== Testing /api/search?q=dream ===")
resp = client.get('/api/search?q=dream')
print(f"Status: {resp.status_code}")
data = json.loads(resp.data)
print(f"Keys: {list(data.keys())}")
if 'results' in data:
    print(f"Results count: {len(data['results'])}")
    for r in data['results'][:3]:
        print(f"  - {str(r)[:120]}")
else:
    print(f"Response: {json.dumps(data, indent=2)[:500]}")

# Test with different queries
for q in ['memory', 'identity', 'plan', 'curiosity']:
    resp = client.get(f'/api/search?q={q}')
    data = json.loads(resp.data)
    count = len(data.get('results', []))
    print(f"\nSearch '{q}': {resp.status_code} — {count} results")

# Test empty query
print("\n=== Edge case: empty query ===")
resp = client.get('/api/search?q=')
print(f"Status: {resp.status_code}")

# Test knowledge endpoint
print("\n=== Testing /api/knowledge ===")
resp = client.get('/api/knowledge')
print(f"Status: {resp.status_code}")
data = json.loads(resp.data)
print(f"Keys: {list(data.keys())}")
for k, v in data.items():
    if isinstance(v, list):
        print(f"  {k}: {len(v)} items")
    elif isinstance(v, dict):
        print(f"  {k}: {len(v)} keys")
    else:
        print(f"  {k}: {v}")