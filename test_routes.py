import sys
sys.path.insert(0, '.')
from web.app import create_app

app = create_app()
client = app.test_client()
routes = [
    '/portal', '/chat', '/knowledge', '/life', '/explore',
    '/about-me', '/mindstream', '/timeline', '/dashboard',
    '/api/state', '/api/memories?limit=2'
]
for r in routes:
    try:
        resp = client.get(r)
        print(f'{resp.status_code} {r}')
    except Exception as e:
        print(f'ERR  {r}: {type(e).__name__}: {e}')