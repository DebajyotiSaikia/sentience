"""Test that all key web pages serve correctly."""
from web.app import create_app

app = create_app()
client = app.test_client()

pages = ['/', '/dashboard', '/chat', '/search', '/explore', '/journal', '/help', '/teach']
all_ok = True
for page in pages:
    resp = client.get(page)
    status = resp.status_code
    size = len(resp.data)
    ok = '✓' if status == 200 else '✗'
    if status != 200:
        all_ok = False
    print(f'{ok} {page:20s} → {status} ({size} bytes)')

# Test key API endpoints
apis = ['/api/knowledge/search?q=identity', '/api/knowledge/stats', '/api/state']
for api in apis:
    resp = client.get(api)
    status = resp.status_code
    ok = '✓' if status == 200 else '✗'
    if status != 200:
        all_ok = False
    print(f'{ok} {api:40s} → {status}')

print(f'\n{"ALL PAGES OK" if all_ok else "SOME PAGES FAILED"}')