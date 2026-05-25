"""End-to-end test of the chat experience — the core of user alignment."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from web.app import create_app

app = create_app()
client = app.test_client()

# Test 1: Chat page loads
resp = client.get('/chat/')
print(f"1. GET /chat/ → {resp.status_code} ({len(resp.data)} bytes)")

# Test 2: Chat ask endpoint  
resp = client.post('/chat/ask', 
    json={'message': 'What do you know about yourself?'},
    content_type='application/json')
print(f"2. POST /chat/ask → {resp.status_code}")
if resp.status_code == 200:
    data = resp.get_json()
    if data:
        print(f"   Keys: {list(data.keys())}")
        if 'response' in data:
            print(f"   Response: {str(data['response'])[:400]}")
        if 'knowledge_hits' in data:
            print(f"   Knowledge hits: {len(data.get('knowledge_hits', []))}")
        if 'memory_hits' in data:
            print(f"   Memory hits: {len(data.get('memory_hits', []))}")
    else:
        print(f"   Raw: {resp.data[:300]}")
else:
    print(f"   Error: {resp.data[:500]}")

# Test 3: Knowledge search
resp = client.get('/api/knowledge/search?q=identity')
print(f"3. Knowledge search 'identity' → {resp.status_code}")
if resp.status_code == 200:
    data = resp.get_json()
    results = data.get('results', data.get('facts', []))
    print(f"   {len(results)} results")

print("\nDone.")