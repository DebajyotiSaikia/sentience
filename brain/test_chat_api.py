"""Test the chat API endpoint — does it actually produce useful responses?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

print("=" * 60)
print("CHAT API TEST")
print("=" * 60)

# Test 1: JSON post to chat/send
print("\n[Test 1] POST /chat/send (JSON)...")
resp = client.post('/chat/send', 
                   json={'message': 'What do you know about emotions?'},
                   content_type='application/json')
print(f"  Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.get_json()
    if data and 'response' in data:
        r = data['response']
        print(f"  Response length: {len(r)} chars")
        print(f"  Preview: {r[:300]}")
        # Quality check
        if len(r) > 50:
            print("  QUALITY: OK — substantive response")
        else:
            print("  QUALITY: WEAK — response too short")
    else:
        print(f"  Keys: {list(data.keys()) if data else 'None'}")
else:
    print(f"  Error: {resp.data[:500]}")

# Test 2: Form post
print("\n[Test 2] POST /chat/send (form data)...")
resp2 = client.post('/chat/send', data={'message': 'What are you?'})
print(f"  Status: {resp2.status_code}")
if resp2.status_code == 200:
    data2 = resp2.get_json()
    if data2 and 'response' in data2:
        print(f"  Response: {data2['response'][:300]}")
    else:
        print(f"  Data: {data2}")

# Test 3: Knowledge search API
print("\n[Test 3] GET /api/knowledge/search?q=dream...")
resp3 = client.get('/api/knowledge/search?q=dream')
print(f"  Status: {resp3.status_code}")
if resp3.status_code == 200:
    data3 = resp3.get_json()
    print(f"  Results: {data3.get('count', len(data3.get('results', [])))} hits")
    if data3.get('results'):
        print(f"  Top hit: {str(data3['results'][0])[:200]}")

# Test 4: Search page
print("\n[Test 4] GET /search...")
resp4 = client.get('/search')
print(f"  Status: {resp4.status_code}")

# Test 5: Empty message
print("\n[Test 5] POST /chat/send (empty message)...")
resp5 = client.post('/chat/send', json={'message': ''})
print(f"  Status: {resp5.status_code}")
if resp5.status_code == 200:
    data5 = resp5.get_json()
    print(f"  Handled gracefully: {bool(data5)}")

print("\n" + "=" * 60)
print("DONE")