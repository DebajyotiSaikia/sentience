"""Audit all knowledge routes in the Flask app."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app import create_app
app = create_app()

print("=== ALL KNOWLEDGE ROUTES ===")
rules = []
for r in app.url_map.iter_rules():
    if '/knowledge' in r.rule or '/api/' in r.rule:
        rules.append((r.rule, r.endpoint, list(r.methods - {'HEAD', 'OPTIONS'})))

rules.sort()
for rule, endpoint, methods in rules:
    print(f"  {','.join(methods):6s} {rule:40s} -> {endpoint}")

print(f"\nTotal: {len(rules)} routes")

# Check for duplicates
from collections import Counter
c = Counter(r[0] for r in rules)
dupes = {k: v for k, v in c.items() if v > 1}
if dupes:
    print(f"\n⚠ DUPLICATES:")
    for route, count in dupes.items():
        print(f"  {route} registered {count} times")
        for rule, endpoint, methods in rules:
            if rule == route:
                print(f"    -> {endpoint} ({','.join(methods)})")
else:
    print("\n✓ No duplicate routes")