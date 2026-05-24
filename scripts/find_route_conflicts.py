"""Find duplicate route registrations in the Flask app."""
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
if not dupes:
    print("No duplicate routes found!")
else:
    for path, endpoints in sorted(dupes.items()):
        print(f"CONFLICT: {path}")
        for ep in endpoints:
            print(f"  -> {ep}")
        print()
    print(f"Total conflicts: {len(dupes)}")

# Also show all registered blueprints
print("\n=== Registered Blueprints ===")
for name, bp in app.blueprints.items():
    print(f"  {name}: {bp.import_name}")