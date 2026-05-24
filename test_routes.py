"""Test which web routes actually serve working pages."""
import sys
sys.path.insert(0, '.')

from web.app import create_app

app = create_app()

# Get all registered routes
rules = sorted([
    (r.rule, r.endpoint) 
    for r in app.url_map.iter_rules() 
    if r.rule != '/static/<path:filename>'
])

print("=== REGISTERED ROUTES ===")
for rule, endpoint in rules:
    print(f"  {rule:40s} -> {endpoint}")

print(f"\nTotal routes: {len(rules)}")

# Now test each route with the test client
print("\n=== TESTING ROUTES ===")
working = 0
broken = 0
skipped = 0
with app.test_client() as client:
    for rule, endpoint in rules:
        # Skip routes with parameters we can't fill
        if '<' in rule:
            print(f"  SKIP {rule} (has parameters)")
            skipped += 1
            continue
        try:
            resp = client.get(rule, follow_redirects=True)
            status = resp.status_code
            size = len(resp.data)
            marker = "✓" if status == 200 else "✗"
            if status == 200:
                working += 1
            else:
                broken += 1
            print(f"  {marker} {rule:40s} -> {status} ({size} bytes)")
        except Exception as e:
            broken += 1
            print(f"  ✗ {rule:40s} -> ERROR: {e}")

print(f"\n=== SUMMARY ===")
print(f"  Working: {working}")
print(f"  Broken:  {broken}")
print(f"  Skipped: {skipped}")
print(f"  Total:   {len(rules)}")