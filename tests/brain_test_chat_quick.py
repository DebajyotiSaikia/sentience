"""Quick chat endpoint test — verifies the actual routes the frontend uses."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# Test 1: Chat page loads
resp = client.get('/chat')
print(f"GET /chat: {resp.status_code}")

# Test 2: Chat ask endpoint (what frontend actually uses)
resp = client.post('/chat/ask',
    data=json.dumps({'message': 'What are you?'}),
    content_type='application/json')
print(f"POST /chat/ask: {resp.status_code}")
data = json.loads(resp.get_data(as_text=True))
print(f"  Keys: {list(data.keys())}")
if 'response' in data:
    print(f"  Response preview: {data['response'][:200]}...")
elif 'error' in data:
    print(f"  Error: {data['error']}")

# Test 3: Starters
resp = client.get('/chat/starters')
print(f"GET /chat/starters: {resp.status_code}")

# Test 4: Home page
resp = client.get('/')
print(f"GET /: {resp.status_code}")
body = resp.get_data(as_text=True)
print(f"  Home page size: {len(body)} chars")

# Test 5: Key API endpoints
for path in ['/api/state', '/api/search?q=identity', '/api/knowledge/facts']:
    resp = client.get(path)
    print(f"GET {path}: {resp.status_code}")

print("\nDone.")