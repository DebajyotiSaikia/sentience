"""Map all API routes and detect conflicts."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
app = create_app()

routes = {}
for rule in app.url_map.iter_rules():
    path = rule.rule
    ep = rule.endpoint
    if path not in routes:
        routes[path] = []
    routes[path].append(ep)

print("=== ALL API/KNOWLEDGE ROUTES ===")
for path in sorted(routes):
    if '/api/' in path or '/knowledge' in path or '/search' in path or '/ask' in path or '/health' in path:
        eps = routes[path]
        flag = ' ⚠ CONFLICT' if len(eps) > 1 else ''
        print(f"  {path}: {eps}{flag}")

print(f"\n=== TOTAL ROUTES: {len(routes)} ===")

# Show conflicts
conflicts = {p: e for p, e in routes.items() if len(e) > 1}
if conflicts:
    print(f"\n⚠ {len(conflicts)} ROUTE CONFLICTS:")
    for p, eps in sorted(conflicts.items()):
        print(f"  {p}: {eps}")
else:
    print("\n✅ No route conflicts detected.")