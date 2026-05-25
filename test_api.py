"""Quick functional test for the web API endpoints."""
from web.app import create_app
import json

app = create_app()

with app.test_client() as c:
    # Test search
    r = c.get('/api/search?q=dream')
    print(f'Search status: {r.status_code}')
    data = json.loads(r.data)
    results = data.get('results', [])
    print(f'Search results: {len(results)}')
    if results:
        print(f'  First: {results[0]["content"][:80]}')
    
    # Test stats
    r2 = c.get('/api/stats')
    print(f'Stats status: {r2.status_code}')
    stats = json.loads(r2.data)
    print(f'Stats keys: {list(stats.keys())}')
    for k, v in stats.items():
        if isinstance(v, (int, float)):
            print(f'  {k}: {v}')
    
    # Test categories
    r3 = c.get('/api/categories')
    print(f'Categories status: {r3.status_code}')
    cats = json.loads(r3.data)
    print(f'Categories: {list(cats.get("categories", {}).keys())[:5]}')
    
    # Test recent
    r4 = c.get('/api/recent?limit=3')
    print(f'Recent status: {r4.status_code}')
    recent = json.loads(r4.data)
    print(f'Recent items: {len(recent.get("items", []))}')

    print('\n✓ All API endpoints responding')