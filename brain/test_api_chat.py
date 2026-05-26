"""Test the /api/chat endpoint end-to-end."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
import json

app = create_app()
client = app.test_client()

# Test 1: POST with a message
print("[Test 1] POST /api/chat with message...")
resp = client.post('/api/chat',
    data=json.dumps({'message': 'What do you know about yourself?'}),
    content_type='application/json')
print(f"  Status: {resp.status_code}")
data = resp.get_json()
if data:
    print(f"  Keys: {list(data.keys())}")
    if 'response' in data:
        preview = str(data['response'])[:200]
        print(f"  Response: {preview}")
    if 'error' in data:
        print(f"  Error: {data['error']}")

# Test 2: Empty message should return 400
print("\n[Test 2] POST /api/chat with empty message...")
resp2 = client.post('/api/chat',
    data=json.dumps({'message': ''}),
    content_type='application/json')
print(f"  Status: {resp2.status_code} (expected 400)")

# Test 3: No body
print("\n[Test 3] POST /api/chat with no body...")
resp3 = client.post('/api/chat')
print(f"  Status: {resp3.status_code} (expected 400)")

# Test 4: GET should fail (method not allowed)
print("\n[Test 4] GET /api/chat (should be 405)...")
resp4 = client.get('/api/chat')
print(f"  Status: {resp4.status_code} (expected 405)")

print("\n=== All API chat tests complete ===")