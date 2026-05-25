"""Audit all Flask routes — find duplicates and conflicts."""
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

print("=== ALL ROUTES ===")
for path in sorted(routes):
    eps = routes[path]
    flag = " ⚠ CONFLICT" if len(eps) > 1 else ""
    print(f"  {path:45s} -> {', '.join(eps)}{flag}")

print(f"\n=== SUMMARY ===")
print(f"Total routes: {len(routes)}")
conflicts = {p: e for p, e in routes.items() if len(e) > 1}
print(f"Conflicts: {len(conflicts)}")
for p, eps in conflicts.items():
    print(f"  ⚠ {p}: {eps}")