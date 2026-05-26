"""Test that the knowledge explorer page renders correctly."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app import create_app

app = create_app()
client = app.test_client()

# Test knowledge explorer page
resp = client.get('/knowledge')
print(f"Status: {resp.status_code}")
print(f"Length: {len(resp.data)} bytes")

html = resp.data.decode()

checks = [
    ('nav' in html.lower(), 'Has navigation'),
    ('knowledge' in html.lower(), 'Has knowledge content'),
    ('search' in html.lower(), 'Has search functionality'),
    ('base.html' not in html, 'Template rendered (no raw jinja)'),
    ('<!DOCTYPE' in html or '<!doctype' in html, 'Valid HTML document'),
    ('<title>' in html.lower(), 'Has title tag'),
]

all_ok = True
for ok, label in checks:
    status = '\u2713' if ok else '\u2717'
    print(f"  {status} {label}")
    if not ok:
        all_ok = False

if resp.status_code != 200:
    print("\n--- First 500 chars ---")
    print(html[:500])

# Test search API
resp2 = client.get('/knowledge/search?q=consciousness')
print(f"\nSearch API: {resp2.status_code}")
if resp2.status_code == 200:
    import json
    data = json.loads(resp2.data)
    print(f"  Results: {len(data.get('results', data.get('facts', [])))} facts found")

print(f"\n{'ALL PASS' if all_ok and resp.status_code == 200 else 'ISSUES FOUND'}")