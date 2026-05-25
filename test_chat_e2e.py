"""End-to-end test of the chat/talk API — the core user interaction."""
from web.app import create_app

app = create_app()
with app.test_client() as c:
    # Test 1: POST to /api/talk
    r = c.post('/api/talk', json={'message': 'What do you know about yourself?'})
    print(f'POST /api/talk → {r.status_code}')
    data = r.get_json()
    if data:
        print(f'  Keys: {list(data.keys())}')
        resp = data.get('response', data.get('reply', data.get('message', '')))
        print(f'  Response: {repr(resp[:300]) if resp else "(empty)"}')
    else:
        print(f'  Raw: {r.data[:300]}')
    
    # Test 2: GET /chat page
    r2 = c.get('/chat')
    print(f'\nGET /chat → {r2.status_code}')
    print(f'  Content length: {len(r2.data)} bytes')
    
    # Test 3: Search API
    r3 = c.get('/api/knowledge/search?q=identity')
    print(f'\nGET /api/knowledge/search?q=identity → {r3.status_code}')
    d3 = r3.get_json()
    if d3:
        results = d3.get('results', [])
        print(f'  Results: {len(results)}')
        if results:
            print(f'  First: {repr(str(results[0])[:200])}')
    
    # Test 4: State API
    r4 = c.get('/api/state')
    print(f'\nGET /api/state → {r4.status_code}')
    d4 = r4.get_json()
    if d4:
        print(f'  Keys: {list(d4.keys())}')

print('\n✓ All tests completed')