"""Quick diagnostic: check for duplicate routes in the Flask app."""
from collections import Counter
from web.app import create_app

app = create_app()
routes = []
for r in app.url_map.iter_rules():
    if r.rule.startswith('/static'):
        continue
    methods = sorted(r.methods - {'OPTIONS', 'HEAD'})
    routes.append((r.rule, methods))

route_rules = [r[0] for r in routes]
dupes = {r: c for r, c in Counter(route_rules).items() if c > 1}

print(f"Total routes: {len(routes)}")
print(f"Duplicate routes: {len(dupes)}")
for r, c in sorted(dupes.items()):
    print(f"  {c}x {r}")

if not dupes:
    print("No duplicates — clean!")