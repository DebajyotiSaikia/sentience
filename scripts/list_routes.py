"""List all Flask routes to identify duplicates/conflicts."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
app = create_app()

routes = []
for rule in app.url_map.iter_rules():
    methods = ','.join(sorted(rule.methods - {'OPTIONS', 'HEAD'}))
    routes.append((rule.rule, rule.endpoint, methods))

routes.sort()

# Find duplicates
from collections import Counter
path_counts = Counter(r[0] for r in routes)
dupes = {p for p, c in path_counts.items() if c > 1}

print(f"Total routes: {len(routes)}")
if dupes:
    print(f"\n⚠ DUPLICATE PATHS ({len(dupes)}):")
    for d in sorted(dupes):
        print(f"  {d}")
        for path, endpoint, methods in routes:
            if path == d:
                print(f"    → {endpoint} [{methods}]")

print(f"\nAll routes:")
for path, endpoint, methods in routes:
    flag = " ⚠ DUP" if path in dupes else ""
    print(f"  {methods:8s} {path:50s} → {endpoint}{flag}")