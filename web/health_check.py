"""Route health check — which pages actually work?"""
import sys
sys.path.insert(0, '/workspace')

from web.app import create_app

app = create_app()

routes_to_check = [
    '/', '/dashboard', '/search', '/chat', '/explore',
    '/about', '/life', '/essays', '/wonder', '/briefing',
    '/talk', '/mind', '/pulse', '/portrait', '/dialogue',
    '/weather', '/knowledge', '/timeline', '/diagnostics',
    '/mindstream', '/collaborate', '/graph'
]

with app.test_client() as client:
    print('=== ROUTE HEALTH CHECK ===')
    working = []
    broken = []
    for route in routes_to_check:
        try:
            resp = client.get(route)
            if resp.status_code == 200:
                status = '✓ 200'
                working.append(route)
            elif resp.status_code in (301, 302, 308):
                status = f'→ {resp.status_code}'
                working.append(route)
            else:
                status = f'✗ {resp.status_code}'
                broken.append((route, resp.status_code))
        except Exception as e:
            status = f'✗ {str(e)[:80]}'
            broken.append((route, str(e)[:40]))
        print(f'  {status}  {route}')

    print(f'\n=== SUMMARY ===')
    print(f'  Working: {len(working)}/{len(routes_to_check)}')
    print(f'  Broken:  {len(broken)}')
    if broken:
        print(f'\n  Broken routes:')
        for r, reason in broken:
            print(f'    {r} — {reason}')