"""Test: can users actually talk to me and get useful responses?"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
app = create_app()
client = app.test_client()

print("=== Chat Response Quality Test ===\n")

# Test 1: POST /api/chat
print("--- POST /api/chat ---")
resp = client.post('/api/chat', 
    data=json.dumps({'message': 'What do you know about consciousness?'}),
    content_type='application/json')
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.get_json()
    print(f"Keys: {list(data.keys()) if data else 'None'}")
    if data and 'response' in data:
        print(f"Response: {data['response'][:300]}")
    elif data:
        print(f"Data: {json.dumps(data, indent=2)[:300]}")
else:
    print(f"Body: {resp.data[:200]}")

# Test 2: POST /chat/ask
print("\n--- POST /chat/ask ---")
resp2 = client.post('/chat/ask',
    data=json.dumps({'message': 'What are you?'}),
    content_type='application/json')
print(f"Status: {resp2.status_code}")
if resp2.status_code == 200:
    data2 = resp2.get_json()
    print(f"Keys: {list(data2.keys()) if data2 else 'None'}")
    if data2 and 'response' in data2:
        print(f"Response: {data2['response'][:300]}")
    elif data2:
        print(f"Data: {json.dumps(data2, indent=2)[:300]}")
else:
    print(f"Body: {resp2.data[:200]}")

# Test 3: GET /chat/ (should render page)
print("\n--- GET /chat/ ---")
resp3 = client.get('/chat/')
print(f"Status: {resp3.status_code}")
print(f"Content length: {len(resp3.data)} bytes")
if resp3.status_code == 200:
    html = resp3.data.decode('utf-8', errors='replace')
    # Check for key elements
    has_input = 'input' in html.lower() or 'textarea' in html.lower()
    has_send = 'send' in html.lower() or 'submit' in html.lower()
    print(f"Has input field: {has_input}")
    print(f"Has send/submit: {has_send}")

# Test 4: Knowledge search (user alignment)
print("\n--- GET /api/knowledge/search?q=consciousness ---")
resp4 = client.get('/api/knowledge/search?q=consciousness')
print(f"Status: {resp4.status_code}")
if resp4.status_code == 200:
    data4 = resp4.get_json()
    if isinstance(data4, list):
        print(f"Results: {len(data4)} items")
        for item in data4[:3]:
            if isinstance(item, dict):
                print(f"  - {str(item.get('fact', item.get('content', item)))[:100]}")
    elif isinstance(data4, dict):
        print(f"Keys: {list(data4.keys())}")
        results = data4.get('results', data4.get('facts', []))
        print(f"Results: {len(results)} items")

# Test 5: Knowledge page
print("\n--- GET /knowledge ---")
resp5 = client.get('/knowledge')
print(f"Status: {resp5.status_code}")
if resp5.status_code == 200:
    print(f"Content length: {len(resp5.data)} bytes")