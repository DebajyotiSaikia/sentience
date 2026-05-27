"""Test the actual /chat/ask endpoint that the frontend uses."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app import create_app

app = create_app()
client = app.test_client()

# Test 1: GET /chat/ should work
r = client.get('/chat/')
print(f"GET /chat/ => {r.status_code}")
assert r.status_code == 200, f"Expected 200, got {r.status_code}"

# Test 2: POST /chat/ask should work  
r = client.post('/chat/ask', json={'message': 'Hello, what are you?'})
print(f"POST /chat/ask => {r.status_code}")
print(f"  Response: {r.get_json()}")
assert r.status_code == 200, f"Expected 200, got {r.status_code}"

data = r.get_json()
assert data is not None, "Response should be JSON"
assert 'response' in data or 'reply' in data or 'message' in data, f"Unexpected keys: {list(data.keys())}"

# Test 3: POST /chat/starters should work
r = client.get('/chat/starters')
print(f"GET /chat/starters => {r.status_code}")

# Test 4: GET /chat/status should work
r = client.get('/chat/status')
print(f"GET /chat/status => {r.status_code}")

print("\n✅ All chat endpoint tests passed!")