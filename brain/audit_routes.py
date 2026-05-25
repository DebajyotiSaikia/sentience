"""Route audit — find duplicate/conflicting routes in the web app."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
from collections import Counter

app = create_app()

endpoints = []
for rule in app.url_map.iter_rules():
    if rule.endpoint != 'static':
        endpoints.append((rule.rule, rule.endpoint))

paths = Counter(r[0] for r in endpoints)
dupes = {p: c for p, c in paths.items() if c > 1}

if dupes:
    print("=== DUPLICATE ROUTES ===")
    for p, c in sorted(dupes.items()):
        print(f"\n  {p}  ({c} definitions)")
        for rule, ep in endpoints:
            if rule == p:
                print(f"    -> endpoint: {ep}")
else:
    print("No duplicate routes found.")

print(f"\nTotal routes: {len(endpoints)}")