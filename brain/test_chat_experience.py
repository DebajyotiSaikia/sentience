"""Test what a user actually experiences when chatting with XTAgent."""
import json
from web.app import create_app

app = create_app()
client = app.test_client()

# Test 1: Chat API endpoint
print("=== Test 1: POST /api/chat ===")
r = client.post('/api/chat', 
    json={'message': 'What do you know about consciousness?'},
    content_type='application/json')
print(f"Status: {r.status_code}")
data = r.get_json()
if data:
    print(f"Response: {json.dumps(data, indent=2)[:1500]}")
else:
    print(f"Raw: {r.data[:500]}")

# Test 2: Knowledge search
print("\n=== Test 2: GET /api/knowledge/search?q=consciousness ===")
r = client.get('/api/knowledge/search?q=consciousness')
print(f"Status: {r.status_code}")
data = r.get_json()
if data:
    print(f"Results: {json.dumps(data, indent=2)[:1000]}")

# Test 3: Knowledge page loads
print("\n=== Test 3: GET /knowledge ===")
r = client.get('/knowledge')
print(f"Status: {r.status_code}, Size: {len(r.data)} bytes")

# Test 4: Chat page loads
print("\n=== Test 4: GET /chat ===")
r = client.get('/chat')
print(f"Status: {r.status_code}, Size: {len(r.data)} bytes")

# Test 5: Help page
print("\n=== Test 5: GET /help ===")
r = client.get('/help')
print(f"Status: {r.status_code}, Size: {len(r.data)} bytes")

# Test 6: About page  
print("\n=== Test 6: GET /about ===")
r = client.get('/about')
print(f"Status: {r.status_code}, Size: {len(r.data)} bytes")

print("\n=== Done ===")