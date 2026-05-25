from web.app import create_app
from collections import defaultdict

app = create_app()
routes = defaultdict(list)
for r in app.url_map.iter_rules():
    routes[r.rule].append(r.endpoint)

print("=== DUPLICATE ROUTES ===")
found = False
for rule, eps in sorted(routes.items()):
    if len(eps) > 1:
        found = True
        print(f"  {rule} -> {eps}")

if not found:
    print("  (none)")

print(f"\nTotal routes: {len(list(app.url_map.iter_rules()))}")