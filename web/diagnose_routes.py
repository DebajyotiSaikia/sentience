"""Diagnose duplicate routes in the web app."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()

# Collect routes by rule
from collections import defaultdict
route_map = defaultdict(list)

for rule in app.url_map.iter_rules():
    route_map[rule.rule].append(rule.endpoint)

print(f"Total routes: {sum(len(v) for v in route_map.values())}")
print(f"Unique paths: {len(route_map)}")

# Show duplicates
print("\n=== DUPLICATE ROUTES ===")
for path in sorted(route_map):
    endpoints = route_map[path]
    if len(endpoints) > 1:
        print(f"  {path}:")
        for ep in endpoints:
            print(f"    -> {ep}")

# Show all blueprints registered
print("\n=== REGISTERED BLUEPRINTS ===")
for name, bp in sorted(app.blueprints.items()):
    # Count routes for this blueprint
    bp_routes = [r for r in app.url_map.iter_rules() if r.endpoint.startswith(name + '.')]
    print(f"  {name}: {len(bp_routes)} routes (module: {bp.import_name})")
    for r in sorted(bp_routes, key=lambda x: x.rule):
        print(f"    {r.rule} -> {r.endpoint}")