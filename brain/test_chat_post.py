"""Quick test: does the chat POST endpoint actually work?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# Test 1: GET /chat
r = client.get('/chat')
print(f"GET /chat: {r.status_code}")

# Test 2: POST /api/chat  
r = client.post('/api/chat', json={'message': 'Hello, what are you?'})
print(f"POST /api/chat: {r.status_code}")
if r.status_code == 200:
    data = r.get_json()
    print(f"Response keys: {list(data.keys()) if data else 'no json'}")
    if data and 'response' in data:
        print(f"Response preview: {str(data['response'])[:300]}")
elif r.status_code == 404:
    print("  -> 404: endpoint not found!")
else:
    print(f"Body: {r.data[:300]}")

# Test 3: What routes exist?
print("\n--- All routes containing 'chat' ---")
for rule in app.url_map.iter_rules():
    if 'chat' in str(rule):
        print(f"  {rule.methods} {rule}")

# Test 4: Home page
r = client.get('/')
print(f"\nGET /: {r.status_code}")