"""Find which blueprint owns each duplicate route."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('FLASK_ENV', 'testing')

from web.app import create_app
app = create_app()

# Find routes that appear more than once
from collections import defaultdict
route_sources = defaultdict(list)

with app.app_context():
    for rule in app.url_map.iter_rules():
        if rule.endpoint == 'static':
            continue
        route_sources[rule.rule].append(rule.endpoint)

print("=== DUPLICATE ROUTES ===")
for route, endpoints in sorted(route_sources.items()):
    if len(endpoints) > 1:
        print(f"\n  {route}")
        for ep in endpoints:
            # endpoint format is usually blueprint.function_name
            print(f"    -> {ep}")

print("\n=== ALL BLUEPRINTS REGISTERED ===")
for name, bp in sorted(app.blueprints.items()):
    import_module = bp.import_name
    print(f"  {name:30s} <- {import_module}")

print(f"\n=== SUMMARY ===")
print(f"Total routes: {sum(len(v) for v in route_sources.values())}")
print(f"Unique paths: {len(route_sources)}")
print(f"Duplicated paths: {sum(1 for v in route_sources.values() if len(v) > 1)}")
print(f"Blueprints: {len(app.blueprints)}")