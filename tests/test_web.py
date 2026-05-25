from web.app import create_app

app = create_app()
with app.test_client() as client:
    # Test all knowledge-related routes
    routes_to_test = [
        '/knowledge',
        '/knowledge/graph',
        '/api/knowledge/search?q=dream',
        '/api/knowledge/stats',
        '/api/status',
    ]
    for route in routes_to_test:
        resp = client.get(route)
        status = resp.status_code
        size = len(resp.data)
        marker = '✓' if status == 200 else '✗'
        print(f'{marker} {route:40s} → {status} ({size} bytes)')
        if status != 200 and status != 302:
            print(f'    Error: {resp.data.decode()[:200]}')