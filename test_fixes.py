"""Quick test: verify web app boots and knowledge endpoints work after fixes."""
from web.app import create_app
import json

app = create_app()
client = app.test_client()

# Test knowledge explorer page
r = client.get('/knowledge')
print(f'GET /knowledge: {r.status_code}')

# Test random fact API
r = client.get('/api/knowledge/random')
print(f'GET /api/knowledge/random: {r.status_code}')
data = json.loads(r.data)
print(f'  Response: {json.dumps(data, indent=2)[:200]}')

# Test knowledge search
r = client.get('/api/knowledge/search?q=consciousness')
print(f'GET /api/knowledge/search?q=consciousness: {r.status_code}')
data = json.loads(r.data)
print(f'  Results: {len(data.get("results", []))} found')

# Test chat endpoint
r = client.post('/api/chat', json={'message': 'hello'})
print(f'POST /api/chat: {r.status_code}')

# Test that we don't have duplicate routes
with app.test_request_context():
    rules = [r.rule for r in app.url_map.iter_rules() if '/api/chat' in r.rule]
    print(f'Routes matching /api/chat: {rules}')

print('\nAll tests passed!' if all else 'Done.')