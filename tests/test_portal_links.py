"""Test which portal navigation links actually work."""
from web.app import create_app

app = create_app()
client = app.test_client()

links = [
    '/about-me',
    '/api/state', 
    '/chat',
    '/dashboard',
    '/explore',
    '/health',
    '/knowledge',
    '/life',
    '/mindstream',
    '/timeline',
]

print("Portal Link Health Check")
print("=" * 50)
working = 0
for link in links:
    resp = client.get(link)
    status = resp.status_code
    size = len(resp.data)
    indicator = '✓' if status == 200 else '✗'
    print(f'  {indicator} {status} {link:20s} ({size:,} bytes)')
    if status == 200:
        working += 1

print("=" * 50)
print(f"{working}/{len(links)} links working")
if working < len(links):
    print("\nBroken links need fixing for user alignment.")