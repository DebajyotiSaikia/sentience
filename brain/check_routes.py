"""Check for duplicate knowledge routes in the Flask app."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web.app import create_app

app = create_app()
routes = {}
for rule in app.url_map.iter_rules():
    path = rule.rule
    if 'knowledge' in path.lower() or 'api' in path.lower():
        endpoint = rule.endpoint
        if path not in routes:
            routes[path] = []
        routes[path].append(endpoint)

print("=== Knowledge/API Routes ===")
for path in sorted(routes):
    endpoints = routes[path]
    flag = ' ⚠ DUPLICATE' if len(endpoints) > 1 else ''
    print(f'  {path} -> {endpoints}{flag}')

dupes = {p: e for p, e in routes.items() if len(e) > 1}
if dupes:
    print(f"\n⚠ Found {len(dupes)} duplicate route(s)!")
else:
    print("\n✓ No duplicate routes found.")