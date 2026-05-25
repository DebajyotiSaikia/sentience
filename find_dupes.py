"""Find duplicate routes by actually importing the Flask app."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from web.app import create_app

app = create_app()
from collections import defaultdict

route_map = defaultdict(list)
for rule in app.url_map.iter_rules():
    if rule.endpoint == 'static':
        continue
    route_map[rule.rule].append(rule.endpoint)

print("=== ALL ROUTES ===")
for route in sorted(route_map.keys()):
    endpoints = route_map[route]
    flag = " *** DUPLICATE ***" if len(endpoints) > 1 else ""
    print(f"  {route:40s} -> {', '.join(endpoints)}{flag}")

print(f"\n=== DUPLICATES ===")
dupes = {r: eps for r, eps in route_map.items() if len(eps) > 1}
if not dupes:
    print("  None found!")
else:
    for route, endpoints in sorted(dupes.items()):
        print(f"  {route}: {endpoints}")