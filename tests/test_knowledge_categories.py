"""Test that knowledge categorization works end-to-end."""
import sys
sys.path.insert(0, '.')

from web.app import create_app
import json

app = create_app()
client = app.test_client()

# Test knowledge page loads
r = client.get('/knowledge')
print(f'Knowledge page: {r.status_code} ({len(r.data)} bytes)')

# Test knowledge API
r2 = client.get('/api/knowledge')
print(f'Knowledge API: {r2.status_code}')

data = json.loads(r2.data)
if 'facts' in data:
    cats = {}
    for f in data['facts']:
        c = f.get('category', f.get('source', '?'))
        cats[c] = cats.get(c, 0) + 1
    print(f'Total facts: {len(data["facts"])}')
    print(f'Categories: {dict(sorted(cats.items(), key=lambda x: -x[1]))}')
    # Show a sample from each category
    seen = set()
    for f in data['facts']:
        c = f.get('category', '?')
        if c not in seen:
            seen.add(c)
            snippet = f['fact'][:80] if f['fact'] else '(empty)'
            print(f'  [{c}] {snippet}')
else:
    print(f'API response keys: {list(data.keys())}')

# Test search
r3 = client.get('/api/knowledge/search?q=consciousness')
print(f'\nSearch "consciousness": {r3.status_code}')
s_data = json.loads(r3.data)
if 'results' in s_data:
    print(f'  Found {len(s_data["results"])} results')
    for res in s_data['results'][:3]:
        print(f'  - {res.get("fact", "")[:70]}')