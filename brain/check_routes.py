"""Check for duplicate routes in the Flask app."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
app = create_app()

routes = {}
for rule in app.url_map.iter_rules():
    key = (rule.rule, tuple(sorted(rule.methods - {'OPTIONS', 'HEAD'})))
    if key not in routes:
        routes[key] = []
    routes[key].append(rule.endpoint)

dupes = {k: v for k, v in routes.items() if len(v) > 1}
if dupes:
    print("=== DUPLICATE ROUTES ===")
    for (path, methods), endpoints in sorted(dupes.items()):
        print(f"  {path} [{','.join(methods)}] -> {endpoints}")
else:
    print("No duplicate routes found.")

print(f"\nTotal routes: {len(list(app.url_map.iter_rules()))}")

# Also show all /api/knowledge* routes
print("\n=== Knowledge-related routes ===")
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    if 'knowledge' in rule.rule.lower():
        print(f"  {rule.rule} [{','.join(sorted(rule.methods - {'OPTIONS','HEAD'}))}] -> {rule.endpoint}")