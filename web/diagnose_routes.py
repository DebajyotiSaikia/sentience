"""Diagnose route conflicts and duplication in the web app."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()

# Collect all routes
routes = {}
duplicates = []
for rule in app.url_map.iter_rules():
    endpoint = rule.endpoint
    path = rule.rule
    methods = ','.join(sorted(rule.methods - {'OPTIONS', 'HEAD'}))
    key = f"{methods} {path}"
    
    if key in routes:
        duplicates.append((key, routes[key], endpoint))
    else:
        routes[key] = endpoint

print(f"=== Total routes: {len(routes)} ===\n")

# Group by blueprint
by_blueprint = {}
for key, endpoint in sorted(routes.items()):
    bp = endpoint.split('.')[0] if '.' in endpoint else '(main)'
    by_blueprint.setdefault(bp, []).append((key, endpoint))

for bp, bp_routes in sorted(by_blueprint.items()):
    print(f"\n--- Blueprint: {bp} ({len(bp_routes)} routes) ---")
    for key, endpoint in bp_routes:
        print(f"  {key:50s} -> {endpoint}")

if duplicates:
    print(f"\n=== DUPLICATES FOUND: {len(duplicates)} ===")
    for key, ep1, ep2 in duplicates:
        print(f"  {key}: {ep1} vs {ep2}")
else:
    print("\n=== No duplicate routes found ===")

# Check templates
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
templates = []
for root, dirs, files in os.walk(template_dir):
    for f in files:
        if f.endswith('.html'):
            rel = os.path.relpath(os.path.join(root, f), template_dir)
            templates.append(rel)

print(f"\n=== Templates: {len(templates)} ===")
for t in sorted(templates):
    print(f"  {t}")

# Find templates that are NOT referenced by any route
print(f"\n=== Blueprint summary ===")
for bp, bp_routes in sorted(by_blueprint.items()):
    print(f"  {bp}: {len(bp_routes)} routes")