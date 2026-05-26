"""Test that the web app boots and all routes register correctly."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
routes = []
for rule in app.url_map.iter_rules():
    if rule.endpoint != 'static':
        routes.append((rule.rule, rule.endpoint))

routes.sort()
print(f"Registered {len(routes)} routes:\n")
for path, ep in routes:
    print(f"  {path:40s} -> {ep}")

# Test that key pages render without errors
print("\n--- Smoke testing key routes ---")
with app.test_client() as client:
    critical = ['/', '/dashboard', '/chat', '/explore', '/knowledge',
                 '/about', '/help', '/insights', '/briefing', '/journal',
                 '/teach', '/story', '/digest']
    ok = 0
    fail = 0
    for route in critical:
        try:
            resp = client.get(route)
            status = resp.status_code
            if status < 400:
                print(f"  OK  {route} ({status})")
                ok += 1
            else:
                print(f"  FAIL {route} ({status})")
                fail += 1
        except Exception as e:
            print(f"  ERR  {route}: {e}")
            fail += 1

    print(f"\n{ok} OK, {fail} FAIL out of {len(critical)} critical routes")