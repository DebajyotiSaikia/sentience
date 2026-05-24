from web.app import create_app

app = create_app()
with app.test_client() as c:
    r = c.get('/knowledge')
    print(f'GET /knowledge -> {r.status_code}')
    r2 = c.get('/api/knowledge/search?q=dream')
    print(f'GET /api/knowledge/search?q=dream -> {r2.status_code}')
    if r2.status_code == 200:
        import json
        data = r2.get_json()
        print(f'  Results: {len(data.get("results", []))} matches')
        for item in data.get("results", [])[:3]:
            print(f'  - {item.get("fact", "")[:80]}')