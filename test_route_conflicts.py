"""Check for route conflicts in the Flask app."""
from web.app import create_app

app = create_app()
routes = {}
conflicts = []

for rule in app.url_map.iter_rules():
    path = rule.rule
    endpoint = rule.endpoint
    if path in routes:
        conflicts.append((path, routes[path], endpoint))
    routes[path] = endpoint

print(f"Total routes: {len(routes)}")

if conflicts:
    print(f"\nCONFLICTS ({len(conflicts)}):")
    for path, ep1, ep2 in conflicts:
        print(f"  {path}: {ep1} vs {ep2}")
else:
    print("No route conflicts detected.")

print("\nKnowledge/search/API routes:")
for path, ep in sorted(routes.items()):
    if any(k in path.lower() for k in ['knowledge', 'search', 'api']):
        print(f"  {path} -> {ep}")