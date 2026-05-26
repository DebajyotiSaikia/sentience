"""Verify knowledge API returns real data."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# Test knowledge stats
resp = client.get('/api/knowledge/stats')
data = json.loads(resp.data)
print(f"Status: {resp.status_code}")
print(f"Total facts: {data.get('total_facts', 'MISSING')}")
print(f"Total memories: {data.get('total_memories', 'MISSING')}")

if data.get('total_facts', 0) > 0:
    print("PASS — Knowledge stats working")
else:
    print("FAIL — Still reporting 0 facts")

# Test knowledge search
resp2 = client.get('/api/knowledge/search?q=identity')
data2 = json.loads(resp2.data)
print(f"\nSearch 'identity': {len(data2.get('results', []))} results")
if data2.get('results'):
    print(f"  First: {data2['results'][0].get('fact', '')[:80]}")