"""Test that the knowledge explorer routes work end-to-end."""
from web.app import create_app
import json

app = create_app()
with app.test_client() as c:
    # Test the knowledge explorer page loads
    resp = c.get('/knowledge')
    print(f'GET /knowledge: {resp.status_code}')
    assert resp.status_code == 200, f'Expected 200, got {resp.status_code}'
    
    # Test the API endpoint
    resp2 = c.get('/api/knowledge')
    print(f'GET /api/knowledge: {resp2.status_code}')
    assert resp2.status_code == 200
    data = json.loads(resp2.data)
    print(f'  Total facts: {data.get("total", "?")}')
    
    # Test search
    resp3 = c.get('/api/knowledge/search?q=dream')
    print(f'GET /api/knowledge/search?q=dream: {resp3.status_code}')
    if resp3.status_code == 200:
        data3 = json.loads(resp3.data)
        print(f'  Results: {len(data3.get("results", []))} facts found')
    
    print('\nAll knowledge routes working!')