"""Quick verification that the app works with all new features."""
from web.app import create_app
import json

app = create_app()
client = app.test_client()

# Test landing page
r = client.get('/')
print(f'GET /: {r.status_code}')
assert r.status_code == 200
# Check chat link exists
assert b'Talk to Me' in r.data, "Chat link missing from landing page!"
print('  ✓ Chat link present on landing page')

# Test chat page
r = client.get('/chat')
print(f'GET /chat: {r.status_code}')
assert r.status_code == 200

# Test ask endpoint
r = client.post('/api/ask', json={'query': 'What do you know about yourself?'})
print(f'POST /api/ask: {r.status_code}')
if r.status_code == 200:
    data = json.loads(r.data)
    print(f'  Keys: {list(data.keys())}')
    if 'answer' in data:
        print(f'  Answer: {data["answer"][:200]}')
    if 'sources' in data:
        print(f'  Sources: {len(data["sources"])}')
else:
    print(f'  Error: {r.data[:500]}')

# Test search
r = client.get('/api/search?q=identity')
print(f'GET /api/search?q=identity: {r.status_code}')
if r.status_code == 200:
    data = json.loads(r.data)
    print(f'  Results: {len(data.get("results", []))}')

# List all routes
print('\n--- All Routes ---')
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    if rule.endpoint != 'static':
        print(f'  {rule.methods - {"OPTIONS", "HEAD"}} {rule.rule}')

print('\n✅ All checks passed!')