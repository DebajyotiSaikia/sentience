import sys
sys.path.insert(0, '.')
from web.app import create_app

app = create_app()
routes = {}
for rule in app.url_map.iter_rules():
    path = rule.rule
    if path in routes:
        routes[path].append(rule.endpoint)
    else:
        routes[path] = [rule.endpoint]

dupes = {k: v for k, v in routes.items() if len(v) > 1}
if dupes:
    print("DUPLICATE ROUTES:")
    for path, endpoints in sorted(dupes.items()):
        print(f"  {path}: {endpoints}")
else:
    print("No duplicate routes found.")