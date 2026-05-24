"""Inspect what routes Flask actually has registered."""
import sys
sys.path.insert(0, '.')

from web.app import create_app

app = create_app()

print("=== ALL REGISTERED ROUTES ===")
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
    print(f"  {rule.rule:40s} [{methods:10s}] → {rule.endpoint}")

print(f"\nTotal routes: {len(list(app.url_map.iter_rules()))}")

# Now test the specific routes
print("\n=== ROUTE TESTS ===")
client = app.test_client()
tests = [
    ('GET', '/ask'),
    ('POST', '/ask/query'),
    ('GET', '/ask/random'),
    ('GET', '/wonder'),
    ('GET', '/mind'),
    ('GET', '/'),
]
for method, path in tests:
    if method == 'GET':
        resp = client.get(path)
    else:
        resp = client.post(path, json={'question': 'test'})
    print(f"  {method} {path:20s} → {resp.status_code}")