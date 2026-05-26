"""Test all user-facing routes to find broken links."""
from web.app import create_app

app = create_app()
client = app.test_client()

routes = [
    '/help', '/search', '/explore', '/knowledge',
    '/journal', '/chat/', '/teach', '/dashboard',
    '/api/state', '/api/knowledge', '/api/knowledge/search?q=test',
    '/graph',
]

print("Route Health Check:")
print("=" * 50)
for r in routes:
    resp = client.get(r)
    status = resp.status_code
    if status in (301, 302, 308):
        loc = resp.headers.get('Location', '?')
        resp2 = client.get(loc)
        print(f"  {r:35s} {status} -> {resp2.status_code}")
    elif status == 200:
        print(f"  {r:35s} ✓ {status}")
    else:
        print(f"  {r:35s} ✗ {status}")

print("\nDone.")