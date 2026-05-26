"""Test the knowledge API and feedback fixes."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
import json

app = create_app()
client = app.test_client()

# Test 1: Knowledge stats should show real facts
r = client.get('/api/knowledge/stats')
print(f"[1] Knowledge stats: {r.status_code}")
data = json.loads(r.get_data(as_text=True))
print(f"    Total facts: {data.get('total_facts', 'MISSING')}")
print(f"    Pass: {data.get('total_facts', 0) > 0}")

# Test 2: Feedback submit
r2 = client.post('/api/feedback', 
    data=json.dumps({"rating": 5, "comment": "test feedback"}),
    content_type='application/json')
print(f"\n[2] Feedback submit: {r2.status_code}")
print(f"    Pass: {r2.status_code in (200, 201)}")

# Test 3: Search returns results  
r3 = client.get('/api/knowledge/search?q=identity')
print(f"\n[3] Knowledge search: {r3.status_code}")
data3 = json.loads(r3.get_data(as_text=True))
results = data3.get('results', [])
print(f"    Results: {len(results)}")
print(f"    Pass: {len(results) > 0}")

# Test 4: Chat endpoint
r4 = client.post('/api/chat',
    data=json.dumps({"message": "hello"}),
    content_type='application/json')
print(f"\n[4] Chat API: {r4.status_code}")
print(f"    Pass: {r4.status_code == 200}")

# Test 5: Home page has real content
r5 = client.get('/')
html = r5.get_data(as_text=True)
print(f"\n[5] Home page: {r5.status_code}, length={len(html)}")
print(f"    Has 'XTAgent': {'XTAgent' in html}")

print("\n" + "=" * 40)
print("Done.")