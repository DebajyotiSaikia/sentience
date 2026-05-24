"""Test which web routes actually work."""
from web.app import create_app

app = create_app()
client = app.test_client()

# Get all non-static routes
rules = sorted([r.rule for r in app.url_map.iter_rules() if not r.rule.startswith('/static')])

print(f"Total routes: {len(rules)}\n")

working = []
broken = []

for rule in rules:
    # Skip parameterized routes for now
    if '<' in rule:
        continue
    try:
        resp = client.get(rule)
        status = resp.status_code
        if status < 400:
            working.append((rule, status))
        else:
            broken.append((rule, status))
    except Exception as e:
        broken.append((rule, f"ERROR: {e}"))

print(f"=== WORKING ({len(working)}) ===")
for route, status in working:
    print(f"  {status} {route}")

print(f"\n=== BROKEN ({len(broken)}) ===")
for route, status in broken:
    print(f"  {status} {route}")

print(f"\n=== PARAMETERIZED (skipped) ===")
for rule in rules:
    if '<' in rule:
        print(f"  {rule}")