from web.app import create_app

app = create_app()
with app.test_client() as c:
    # Test the API search endpoint (correct path)
    resp = c.get('/api/knowledge/search?q=dream')
    print('Search status:', resp.status_code)
    print('Content-Type:', resp.content_type)
    if resp.status_code == 200:
        import json
        data = json.loads(resp.data)
        print('Results:', len(data.get('results', data.get('facts', []))))
        for item in list(data.get('results', data.get('facts', [])))[:3]:
            if isinstance(item, str):
                print(f'  - {item[:80]}')
            elif isinstance(item, dict):
                print(f'  - {item.get("fact", item.get("text", str(item)))[:80]}')
    else:
        print('Error:', resp.data[:500].decode('utf-8', errors='replace'))

    # Test query endpoint too
    resp2 = c.get('/api/knowledge/query?q=what+do+I+know+about+dreams')
    print('\nQuery status:', resp2.status_code)
    if resp2.status_code == 200:
        import json
        data2 = json.loads(resp2.data)
        print('Query response keys:', list(data2.keys()))

    # Test stats
    resp3 = c.get('/api/knowledge/stats')
    print('\nStats status:', resp3.status_code)
    if resp3.status_code == 200:
        import json
        stats = json.loads(resp3.data)
        print('Stats:', json.dumps(stats, indent=2)[:500])