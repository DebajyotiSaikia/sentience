"""Test actual user-facing functionality — can users chat and search knowledge?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web.app import create_app
import json

app = create_app()
client = app.test_client()

# Test 1: Chat API
print("=== Chat API ===")
r = client.post('/api/chat', 
    json={'message': 'What do you know about consciousness?'},
    content_type='application/json')
print(f"Status: {r.status_code}")
data = json.loads(r.data)
print(f"Response keys: {list(data.keys())}")
if 'response' in data:
    resp = data['response']
    print(f"Response length: {len(resp)}")
    print(f"First 400 chars:\n{resp[:400]}")
    # Quality check
    mentions_consciousness = 'conscious' in resp.lower()
    is_generic = resp.startswith("I don't") or 'not sure' in resp.lower()
    print(f"Mentions consciousness: {mentions_consciousness}")
    print(f"Seems generic/unhelpful: {is_generic}")
elif 'error' in data:
    print(f"Error: {data['error']}")

# Test 2: Knowledge search API
print("\n=== Knowledge Search API ===")
r2 = client.get('/api/knowledge/search?q=consciousness')
print(f"Status: {r2.status_code}")
data2 = json.loads(r2.data)
print(f"Response keys: {list(data2.keys())}")
if 'results' in data2:
    print(f"Results count: {len(data2['results'])}")
    for item in data2['results'][:3]:
        print(f"  - {str(item)[:150]}")

# Test 3: Knowledge explorer page content
print("\n=== Knowledge Explorer Page ===")
r3 = client.get('/knowledge')
print(f"Status: {r3.status_code}")
html = r3.data.decode('utf-8')
print(f"Page size: {len(html)} bytes")
has_search = 'search' in html.lower()
has_facts = 'fact' in html.lower() or 'knowledge' in html.lower()
print(f"Has search functionality: {has_search}")
print(f"Has knowledge content: {has_facts}")

# Test 4: Chat page content
print("\n=== Chat Page ===")
r4 = client.get('/chat')
print(f"Status: {r4.status_code}")
html4 = r4.data.decode('utf-8')
print(f"Page size: {len(html4)} bytes")
has_input = 'input' in html4.lower() or 'textarea' in html4.lower()
has_nav = 'nav' in html4.lower()
print(f"Has input field: {has_input}")
print(f"Has navigation: {has_nav}")