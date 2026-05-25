"""Quick health check for all web routes and APIs."""
from web.app import create_app

app = create_app()
client = app.test_client()

routes = ['/', '/dashboard', '/chat', '/search', '/explore', '/journal', '/teach', '/help']
print('=== Route Health Check ===')
all_ok = True
for route in routes:
    resp = client.get(route)
    status = resp.status_code
    has_nav = b'nav.js' in resp.data or b'nav-bar' in resp.data
    size = len(resp.data)
    symbol = 'OK' if status == 200 else 'FAIL'
    nav_sym = 'NAV' if has_nav else '   '
    print(f'  {symbol} {nav_sym} {route:15s} -> {status} ({size:,} bytes)')
    if status != 200:
        all_ok = False

api_routes = ['/api/state', '/api/search?q=dream', '/api/knowledge/search?q=emotion']
print()
print('=== API Health Check ===')
for route in api_routes:
    resp = client.get(route)
    status = resp.status_code
    is_json = resp.content_type and 'json' in resp.content_type
    symbol = 'OK' if status == 200 and is_json else 'FAIL'
    print(f'  {symbol} {route:40s} -> {status} (json={is_json})')
    if status != 200:
        all_ok = False

print()
print('ALL OK' if all_ok else 'ISSUES FOUND')