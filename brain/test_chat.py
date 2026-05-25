"""Test the chat endpoint end-to-end."""
import sys
sys.path.insert(0, '.')
from web.app import create_app

app = create_app()
client = app.test_client()

# Test 1: GET /chat/ should return 200
resp = client.get('/chat/')
print(f"GET /chat/ => {resp.status_code} ({len(resp.data)} bytes)")

# Test 2: GET /chat/status
resp = client.get('/chat/status')
print(f"GET /chat/status => {resp.status_code}")
if resp.status_code == 200:
    print(f"  body: {resp.get_json()}")

# Test 3: POST /chat/ask with a message
resp = client.post('/chat/ask', 
                    json={'message': 'What do you know about yourself?'},
                    content_type='application/json')
print(f"POST /chat/ask => {resp.status_code}")
if resp.status_code == 200:
    data = resp.get_json()
    if data:
        reply = data.get('response', data.get('reply', str(data)[:200]))
        print(f"  reply: {str(reply)[:300]}")
elif resp.status_code >= 400:
    print(f"  error: {resp.data[:500]}")