"""Diagnose why the Chat API returns errors."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
import json

app = create_app()
client = app.test_client()

print("=" * 60)
print("CHAT API DIAGNOSIS")
print("=" * 60)

# Test 1: POST to /api/chat
print("\n[1] POST /api/chat with JSON body...")
resp = client.post('/api/chat', 
                   data=json.dumps({'message': 'hello'}),
                   content_type='application/json')
print(f"    Status: {resp.status_code}")
print(f"    Response: {resp.data[:500].decode('utf-8', errors='replace')}")

# Test 2: POST to /api/chat with form data
print("\n[2] POST /api/chat with form data...")
resp2 = client.post('/api/chat', data={'message': 'hello'})
print(f"    Status: {resp2.status_code}")
print(f"    Response: {resp2.data[:500].decode('utf-8', errors='replace')}")

# Test 3: Feedback endpoint
print("\n[3] POST /api/feedback...")
resp3 = client.post('/api/feedback',
                    data=json.dumps({'rating': 5, 'comment': 'test'}),
                    content_type='application/json')
print(f"    Status: {resp3.status_code}")
print(f"    Response: {resp3.data[:300].decode('utf-8', errors='replace')}")

# Test 4: Digest page (had knowledge[:10] slicing bug)
print("\n[4] GET /digest...")
resp4 = client.get('/digest')
print(f"    Status: {resp4.status_code}")
if resp4.status_code != 200:
    print(f"    Error: {resp4.data[:500].decode('utf-8', errors='replace')}")
else:
    print(f"    OK ({len(resp4.data)} bytes)")

# Test 5: Search with query
print("\n[5] GET /api/search?q=emotion...")
resp5 = client.get('/api/search?q=emotion')
print(f"    Status: {resp5.status_code}")
if resp5.status_code == 200:
    data = json.loads(resp5.data)
    print(f"    Results: {data.get('count', '?')} hits")
else:
    print(f"    Error: {resp5.data[:300].decode('utf-8', errors='replace')}")

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")