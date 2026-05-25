"""Find all route conflicts in the Flask app."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['TESTING'] = '1'

from web.app import create_app
app = create_app()

rules = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
seen = {}
conflicts = []

print("=== ALL KNOWLEDGE-RELATED ROUTES ===")
for r in rules:
    if 'knowledge' in r.rule.lower() or 'knowledge' in r.endpoint.lower():
        print(f"  {r.rule:50s} -> {r.endpoint}")

print()
print("=== ALL ROUTE CONFLICTS (same path, different endpoints) ===")
for r in rules:
    if r.rule in seen:
        conflicts.append((r.rule, seen[r.rule], r.endpoint))
    seen[r.rule] = r.endpoint

for rule, ep1, ep2 in conflicts:
    print(f"  CONFLICT: {rule}")
    print(f"    ep1: {ep1}")
    print(f"    ep2: {ep2}")

if not conflicts:
    print("  No conflicts found!")

print()
print("=== REGISTERED BLUEPRINTS ===")
for name, bp in app.blueprints.items():
    print(f"  {name}: {bp.import_name}")