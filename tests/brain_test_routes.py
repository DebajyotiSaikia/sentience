"""Quick route health check — which pages work, which don't?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
with app.test_client() as c:
    routes = [
        '/', '/dashboard', '/chat', '/search', '/explore',
        '/journal', '/teach', '/help', '/about', '/knowledge',
        '/briefing', '/insights', '/digest', '/story',
        '/collaborate', '/live', '/talk',
        '/api/state', '/api/search?q=dream', '/api/knowledge/search?q=emotion',
    ]
    ok = 0
    fail = 0
    for route in routes:
        try:
            r = c.get(route)
            status = r.status_code
            marker = '\u2713' if status in (200, 302) else '\u2717'
            if status not in (200, 302):
                fail += 1
                # Get first line of error if 500
                if status == 500:
                    body = r.data.decode('utf-8', errors='replace')[:200]
                    print(f'  {marker} {route:35s} -> {status}  {body[:80]}')
                else:
                    print(f'  {marker} {route:35s} -> {status}')
            else:
                ok += 1
                print(f'  {marker} {route:35s} -> {status}')
        except Exception as e:
            fail += 1
            print(f'  ! {route:35s} -> ERROR: {e}')
    
    print(f'\n  Summary: {ok} OK, {fail} failed out of {len(routes)} routes')