"""List all registered routes in the web app."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web.app import create_app

app = create_app()
routes = []
for rule in app.url_map.iter_rules():
    if rule.endpoint != 'static':
        routes.append((rule.rule, rule.endpoint))
routes.sort()

print("=== ALL REGISTERED ROUTES ===")
for r, e in routes:
    print(f"  {r:45s} -> {e}")
print(f"\nTotal: {len(routes)} routes")

# Show which blueprints are registered
print("\n=== BLUEPRINTS ===")
for name, bp in sorted(app.blueprints.items()):
    print(f"  {name:30s} prefix={bp.url_prefix or '/'}")