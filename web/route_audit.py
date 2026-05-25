"""Route Audit — shows exactly which routes are registered at runtime."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()

# Collect all routes
routes = {}
conflicts = {}

for rule in app.url_map.iter_rules():
    path = rule.rule
    endpoint = rule.endpoint
    methods = ','.join(sorted(rule.methods - {'OPTIONS', 'HEAD'}))
    
    if path not in routes:
        routes[path] = []
    routes[path].append((endpoint, methods))

# Sort and display
print(f"{'PATH':<45} {'ENDPOINT':<40} {'METHODS'}")
print("=" * 120)

for path in sorted(routes.keys()):
    entries = routes[path]
    marker = " ⚠️ CONFLICT" if len(entries) > 1 else ""
    for endpoint, methods in entries:
        print(f"{path:<45} {endpoint:<40} {methods}{marker}")

# Summary
conflict_count = sum(1 for v in routes.values() if len(v) > 1)
print(f"\n{'=' * 120}")
print(f"Total routes: {len(routes)}  |  Conflicts: {conflict_count}")

if conflict_count:
    print("\n⚠️  CONFLICTING ROUTES:")
    for path, entries in sorted(routes.items()):
        if len(entries) > 1:
            print(f"  {path}:")
            for endpoint, methods in entries:
                print(f"    → {endpoint} ({methods})")