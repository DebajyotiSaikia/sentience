"""Test all main web routes respond correctly."""
import sys
sys.path.insert(0, '.')
from web.app import create_app

app = create_app()
client = app.test_client()

routes = ['/', '/search', '/chat', '/help', '/teach', '/explore', '/journal', '/dashboard']
all_ok = True
for route in routes:
    resp = client.get(route)
    status = resp.status_code
    if status in (301, 302):
        loc = resp.headers.get('Location', '?')
        print(f'{route:20s} -> {status} redirect to {loc}')
    else:
        size = len(resp.data)
        ok = 'OK' if status == 200 else 'FAIL'
        if status != 200:
            all_ok = False
        print(f'{route:20s} -> {status} ({size} bytes) {ok}')

print()
print('ALL ROUTES OK' if all_ok else 'SOME ROUTES FAILED')