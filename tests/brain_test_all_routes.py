"""Test all web routes — find what's broken."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
app = create_app()
client = app.test_client()

routes = ['/', '/dashboard', '/chat', '/search', '/explore', '/knowledge',
          '/talk', '/about', '/help', '/teach', '/briefing', '/digest',
          '/insights', '/journal', '/story', '/collaborate', '/live', '/mindstream']

print("=" * 60)
print("ROUTE HEALTH CHECK")
print("=" * 60)

broken = []
for route in routes:
    try:
        resp = client.get(route)
        status = resp.status_code
        size = len(resp.data)
        if status == 200:
            print(f"  OK  {route:20s} -> {status} ({size} bytes)")
        elif status < 400:
            print(f"  ->  {route:20s} -> {status} (redirect)")
        else:
            print(f"  ERR {route:20s} -> {status} ({size} bytes)")
            broken.append((route, status, resp.data[:500].decode('utf-8', errors='replace')))
    except Exception as e:
        print(f"  !!  {route:20s} -> CRASH: {e}")
        broken.append((route, 'CRASH', str(e)))

print(f"\n{'=' * 60}")
print(f"Results: {len(routes) - len(broken)} OK, {len(broken)} broken")

if broken:
    print(f"\n--- BROKEN ROUTES ---")
    for route, status, detail in broken:
        print(f"\n{route} ({status}):")
        print(f"  {detail[:300]}")