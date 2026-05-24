from web.app import create_app

app = create_app()
client = app.test_client()

routes = [
    '/chat', '/knowledge', '/dashboard', '/life', '/explore',
    '/about-me', '/about', '/mindstream', '/timeline', '/health',
    '/api/state', '/wonder', '/graph', '/dreams'
]

print("=== Portal Route Health Check ===")
broken = []
for r in routes:
    resp = client.get(r)
    status = resp.status_code
    # Follow redirects
    location = resp.headers.get('Location', '')
    if status < 400:
        symbol = '✓'
    else:
        symbol = '✗'
        broken.append(r)
    extra = f' → {location}' if location else ''
    print(f'  {symbol} {r} → {status}{extra}')

print(f"\n{len(routes) - len(broken)}/{len(routes)} routes healthy")
if broken:
    print(f"BROKEN: {', '.join(broken)}")
else:
    print("All routes working!")