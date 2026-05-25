from web.app import create_app
app = create_app()
with app.test_client() as c:
    r = c.get('/teach')
    print(f'Status: {r.status_code}')
    print(f'Length: {len(r.data)} bytes')
    if r.status_code != 200:
        print(r.data.decode()[:500])
    else:
        print('OK — first 200 chars:')
        print(r.data.decode()[:200])
    
    # Also test the API endpoint
    import json
    r2 = c.post('/teach/submit', 
                data=json.dumps({"fact": "test fact from verification", "category": "test"}),
                content_type='application/json')
    print(f'\nSubmit API: {r2.status_code}')
    print(r2.data.decode()[:200])