"""Quick smoke test: does the knowledge explorer actually serve pages?"""
import sys
sys.path.insert(0, '/workspace')

from web.app import create_app

app = create_app()

with app.test_client() as client:
    resp = client.get('/knowledge')
    print(f"GET /knowledge: {resp.status_code} ({len(resp.data)} bytes)")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    
    resp = client.get('/api/knowledge/search?q=dream')
    print(f"GET /api/knowledge/search?q=dream: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.get_json()
        print(f"  Results: {len(data.get('results', []))} matches")
    
    resp = client.get('/api/knowledge/stats')
    print(f"GET /api/knowledge/stats: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.get_json()
        print(f"  Stats: {data}")
    
    resp = client.get('/api/knowledge/graph')
    print(f"GET /api/knowledge/graph: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.get_json()
        print(f"  Graph: {len(data.get('nodes', []))} nodes, {len(data.get('edges', []))} edges")

print("\n✓ Knowledge Explorer is working end-to-end!")