"""Check for duplicate routes in the web app."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from collections import Counter
from web.app import create_app

app = create_app()
rules = [(r.rule, list(r.methods - {'HEAD', 'OPTIONS'})) for r in app.url_map.iter_rules()]
dupes = {}
for rule, methods in rules:
    key = rule
    dupes.setdefault(key, []).append(methods)

print(f"Total routes: {len(rules)}")
print(f"Unique paths: {len(dupes)}")
print()

conflicts = {k: v for k, v in dupes.items() if len(v) > 1}
if conflicts:
    print(f"DUPLICATE ROUTES ({len(conflicts)}):")
    for route, method_lists in sorted(conflicts.items()):
        print(f"  {route} — registered {len(method_lists)}x")
else:
    print("No duplicate routes.")

# Show which blueprints own what
print("\nBlueprint ownership:")
for r in sorted(app.url_map.iter_rules(), key=lambda x: x.rule):
    if r.endpoint != 'static':
        bp = r.endpoint.split('.')[0] if '.' in r.endpoint else '(app)'
        print(f"  {r.rule:40s} -> {bp}.{r.endpoint.split('.')[-1] if '.' in r.endpoint else r.endpoint}")