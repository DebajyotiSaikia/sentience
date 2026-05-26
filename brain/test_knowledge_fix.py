"""Verify knowledge_api.py now reads from brain/knowledge.json correctly."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# Test 1: Knowledge stats endpoint
resp = client.get('/api/knowledge/stats')
print(f"[Stats] Status: {resp.status_code}")
if resp.status_code == 200:
    data = json.loads(resp.data)
    print(f"  Total facts: {data.get('total_facts', 'missing')}")
    print(f"  Categories: {len(data.get('categories', {}))}")
else:
    print(f"  Error: {resp.data[:200]}")

# Test 2: Knowledge search
resp = client.get('/api/knowledge/search?q=identity')
print(f"\n[Search 'identity'] Status: {resp.status_code}")
if resp.status_code == 200:
    data = json.loads(resp.data)
    print(f"  Results: {data.get('count', len(data.get('results', [])))}")
    for r in data.get('results', [])[:3]:
        fact = r.get('fact', r.get('content', ''))[:80]
        print(f"  - {fact}")

# Test 3: Knowledge categories
resp = client.get('/api/knowledge/categories')
print(f"\n[Categories] Status: {resp.status_code}")
if resp.status_code == 200:
    data = json.loads(resp.data)
    for cat in list(data.get('categories', {}).keys())[:5]:
        count = data['categories'][cat].get('count', 0)
        print(f"  {cat}: {count} facts")

# Test 4: Chat endpoint
resp = client.post('/api/chat', 
    data=json.dumps({'message': 'What do you know?'}),
    content_type='application/json')
print(f"\n[Chat] Status: {resp.status_code}")
if resp.status_code == 200:
    data = json.loads(resp.data)
    reply = data.get('response', data.get('reply', ''))[:150]
    print(f"  Reply: {reply}")

print("\n--- Done ---")