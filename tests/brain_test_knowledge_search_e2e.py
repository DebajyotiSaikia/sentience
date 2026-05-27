"""Test: Does knowledge search actually work end-to-end?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# Test 1: Knowledge page loads
r = client.get('/knowledge')
print(f"GET /knowledge -> {r.status_code} ({len(r.data)} bytes)")

# Test 2: Search API works
r = client.get('/api/knowledge/search?q=consciousness')
print(f"GET /api/knowledge/search?q=consciousness -> {r.status_code}")
if r.status_code == 200:
    data = r.get_json()
    print(f"  Results: {len(data.get('results', []))} hits")
    for hit in data.get('results', [])[:3]:
        print(f"  - {hit.get('fact', hit.get('text', '???'))[:80]}")
else:
    print(f"  Body: {r.data[:200]}")

# Test 3: Knowledge stats API
r = client.get('/api/knowledge')
print(f"GET /api/knowledge -> {r.status_code}")
if r.status_code == 200:
    data = r.get_json()
    print(f"  Facts: {data.get('total_facts', '?')}")

# Test 4: Chat API with knowledge question
import json
r = client.post('/api/chat', 
    data=json.dumps({'message': 'What do you know about consciousness?'}),
    content_type='application/json')
print(f"POST /api/chat -> {r.status_code}")
if r.status_code == 200:
    data = r.get_json()
    resp = data.get('response', '')[:150]
    print(f"  Response: {resp}")
else:
    print(f"  Error: {r.data[:200]}")