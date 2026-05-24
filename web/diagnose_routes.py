"""Diagnose duplicate routes and their source blueprints."""
from web.app import create_app

app = create_app()

# Collect all routes by path
routes_by_path = {}
for rule in app.url_map.iter_rules():
    if rule.endpoint == 'static':
        continue
    path = rule.rule
    methods = sorted(rule.methods - {"HEAD", "OPTIONS"})
    key = (path, tuple(methods))
    if key not in routes_by_path:
        routes_by_path[key] = []
    routes_by_path[key].append(rule.endpoint)

# Find duplicates
print("=== DUPLICATE ROUTES ===")
dupes_found = 0
for (path, methods), endpoints in sorted(routes_by_path.items()):
    if len(endpoints) > 1:
        dupes_found += 1
        print(f"\n  {path} [{', '.join(methods)}]")
        for ep in endpoints:
            # endpoint format is usually blueprint.function_name
            print(f"    -> {ep}")

if dupes_found == 0:
    print("  None found!")

# Show all blueprints
print(f"\n=== REGISTERED BLUEPRINTS ({len(app.blueprints)}) ===")
for name, bp in sorted(app.blueprints.items()):
    print(f"  {name}: import={bp.import_name}")

# Show total route count
all_routes = [r for r in app.url_map.iter_rules() if r.endpoint != 'static']
print(f"\n=== SUMMARY ===")
print(f"  Total routes: {len(all_routes)}")
print(f"  Unique paths: {len(set(r.rule for r in all_routes))}")
print(f"  Duplicate path groups: {dupes_found}")
print(f"  Blueprints: {len(app.blueprints)}")