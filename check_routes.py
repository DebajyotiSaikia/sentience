"""Map all routes in the web app, find duplicates and overlaps."""
from web.app import create_app

app = create_app()
routes = {}
for rule in app.url_map.iter_rules():
    path = rule.rule
    if path not in routes:
        routes[path] = []
    routes[path].append(rule.endpoint)

dupes = {k: v for k, v in routes.items() if len(v) > 1}
print(f"Total routes: {len(routes)}")
print(f"Duplicate routes: {len(dupes)}")
for path, endpoints in sorted(dupes.items()):
    print(f"  DUPE: {path} -> {endpoints}")

print("\nAll knowledge/search/explore routes:")
for path in sorted(routes):
    if any(k in path.lower() for k in ['knowledge', 'search', 'explore', 'api']):
        print(f"  {path} -> {routes[path]}")

print("\nAll routes by blueprint:")
by_bp = {}
for rule in app.url_map.iter_rules():
    bp = rule.endpoint.split('.')[0] if '.' in rule.endpoint else 'root'
    if bp not in by_bp:
        by_bp[bp] = []
    by_bp[bp].append(rule.rule)

for bp in sorted(by_bp):
    print(f"\n  [{bp}]")
    for r in sorted(by_bp[bp]):
        print(f"    {r}")