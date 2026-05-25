"""Test what a user actually sees on the dashboard."""
from web.app import create_app

app = create_app()
client = app.test_client()

# Get the main dashboard
resp = client.get('/')
html = resp.data.decode()
lines = html.split('\n')

print(f"Status: {resp.status_code}")
print(f"Total lines: {len(lines)}")
print(f"Content length: {len(resp.data)} bytes")
print()

# Show lines 80-end (already saw 0-79)
print("--- LINES 80 onwards ---")
for i, line in enumerate(lines[80:], start=80):
    print(f"{i:4d}: {line}")

print("\n--- ALL ROUTES ---")
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    if rule.endpoint != 'static':
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        print(f"  {methods:6s} {rule.rule:40s} -> {rule.endpoint}")