"""Quick smoke test of web endpoints."""
from web.app import create_app

app = create_app()
c = app.test_client()

routes = [
    ('GET', '/'),
    ('GET', '/chat'),
    ('GET', '/knowledge'),
    ('GET', '/api/knowledge/stats'),
    ('POST', '/chat/ask', {'message': 'hello'}),
]

for entry in routes:
    method = entry[0]
    path = entry[1]
    data = entry[2] if len(entry) > 2 else None
    
    if method == 'GET':
        r = c.get(path)
    else:
        r = c.post(path, json=data, content_type='application/json')
    
    status = 'OK' if r.status_code < 400 else 'FAIL'
    print(f'{status} {method} {path} -> {r.status_code}')
    if r.status_code >= 400:
        # Show first 200 chars of response for debugging
        print(f'     Body: {r.data[:200]}')