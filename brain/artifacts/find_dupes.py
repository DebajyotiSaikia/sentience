"""Find duplicate Flask routes in the XTAgent web app."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from web.app import create_app

app = create_app()
dupes = {}
for rule in app.url_map.iter_rules():
    r = rule.rule
    dupes.setdefault(r, []).append(rule.endpoint)

print("=== DUPLICATE ROUTES ===")
found = False
for route, endpoints in sorted(dupes.items()):
    if len(endpoints) > 1:
        found = True
        print(f"\nDUPE: {route}")
        for ep in endpoints:
            print(f"  -> {ep}")

if not found:
    print("No duplicates found.")

print(f"\nTotal routes: {len(list(app.url_map.iter_rules()))}")