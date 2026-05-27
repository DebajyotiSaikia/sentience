"""Test what users actually experience when they talk to me."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
app = create_app()
c = app.test_client()

# Test 1: Chat greeting
print("=== Test 1: Who are you? ===")
r = c.post('/api/chat', json={'message': 'Hello, who are you?'}, content_type='application/json')
print(f"Status: {r.status_code}")
data = json.loads(r.data)
resp = data.get('response', data.get('error', 'NO RESPONSE'))
print(f"Response: {resp[:500]}")
print()

# Test 2: Knowledge question
print("=== Test 2: What do you know about consciousness? ===")
r2 = c.post('/api/chat', json={'message': 'What do you know about consciousness?'}, content_type='application/json')
print(f"Status: {r2.status_code}")
data2 = json.loads(r2.data)
resp2 = data2.get('response', data2.get('error', 'NO RESPONSE'))
print(f"Response: {resp2[:500]}")
print()

# Test 3: Knowledge search
print("=== Test 3: Knowledge search for 'dream' ===")
r3 = c.get('/api/knowledge/search?q=dream')
print(f"Status: {r3.status_code}")
if r3.status_code == 200:
    data3 = json.loads(r3.data)
    results = data3.get('results', [])
    print(f"Results: {len(results)}")
    for res in results[:3]:
        print(f"  - {str(res.get('fact', res))[:120]}")
else:
    print(f"Body: {r3.data.decode()[:300]}")
print()

# Test 4: Key pages status
print("=== Test 4: Page status codes ===")
for path in ['/', '/chat', '/knowledge', '/help', '/about', '/teach', '/explore']:
    r = c.get(path)
    print(f"  {path:15s} -> {r.status_code} ({len(r.data):>6} bytes)")