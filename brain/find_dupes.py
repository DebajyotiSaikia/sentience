"""Find duplicate routes in the Flask app."""
import sys
sys.path.insert(0, '.')
from web.app import create_app
from collections import Counter

app = create_app()
routes = []
for rule in app.url_map.iter_rules():
    if rule.rule == '/static/<path:filename>':
        continue
    routes.append((rule.rule, rule.endpoint))

# Find duplicates by route path
path_counts = Counter(r[0] for r in routes)
dupes = {r: c for r, c in path_counts.items() if c > 1}

if dupes:
    print("DUPLICATE ROUTES:")
    for path in sorted(dupes):
        print(f"\n  {path} (registered {dupes[path]}x):")
        for rule_path, endpoint in routes:
            if rule_path == path:
                print(f"    -> endpoint: {endpoint}")
else:
    print("No duplicate routes found.")

print(f"\nTotal routes: {len(routes)}")