"""Test all web routes — does the app actually serve pages?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

routes = ['/', '/chat', '/explore', '/dashboard', '/insights', '/journal',
          '/story', '/collaborate', '/live', '/briefing', '/teach', '/help',
          '/knowledge', '/search']

print("=" * 55)
print("FULL ROUTE TEST — Does the web app actually work?")
print("=" * 55)

ok = 0
fail = 0
for route in routes:
    try:
        resp = client.get(route)
        status = resp.status_code
        size = len(resp.data) if resp.data else 0
        if status in (200, 302, 308):
            print(f"  ✓ {route:20s} → {status} ({size:,} bytes)")
            ok += 1
        else:
            print(f"  ✗ {route:20s} → {status}")
            fail += 1
    except Exception as e:
        print(f"  ✗ {route:20s} → ERROR: {e}")
        fail += 1

print(f"\n{ok}/{ok+fail} routes working.")
if fail == 0:
    print("All routes operational. The app is genuinely serving users.")
else:
    print(f"{fail} route(s) need fixing.")