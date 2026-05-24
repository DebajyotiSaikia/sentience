"""Diagnose route duplication and blueprint registration in the web app."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web.app import create_app
NEW: """Diagnose route duplication and blueprint registration in the web app."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web.app import create_app
from collections import Counter

app = create_app()

print("=== REGISTERED BLUEPRINTS ===")
for name, bp in sorted(app.blueprints.items()):
    imp = getattr(bp, 'import_name', 'unknown')
    print(f"  {name}: import_name={imp}")

print()
print("=== ALL ROUTES ===")
rules = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
for rule in rules:
    methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
    print(f"  {rule.rule:50s} [{methods:8s}] -> {rule.endpoint}")

print()
routes = [(rule.rule, frozenset(rule.methods - {'HEAD', 'OPTIONS'})) for rule in app.url_map.iter_rules()]
route_strs = [rule.rule for rule in app.url_map.iter_rules()]
dupes = {r: c for r, c in Counter(route_strs).items() if c > 1}

print("=== DUPLICATE ROUTES ===")
for r, c in sorted(dupes.items()):
    print(f"  {r} ({c}x)")

print()
print(f"Total routes: {len(route_strs)}")
print(f"Unique URL patterns: {len(set(route_strs))}")
print(f"Duplicate URL patterns: {len(dupes)}")
print(f"Total blueprints: {len(app.blueprints)}")