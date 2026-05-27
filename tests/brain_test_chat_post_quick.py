"""Quick test: does POST /chat actually work?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
from web.app import create_app

app = create_app()
c = app.test_client()

# Test POST /chat with JSON
r = c.post('/chat', data=json.dumps({'message': 'hello'}), content_type='application/json')
print(f'POST /chat -> {r.status_code}')
if r.status_code == 200:
    try:
        data = r.get_json()
        print(f'  Response keys: {list(data.keys()) if data else "None"}')
        if data and 'response' in data:
            print(f'  Response text: {str(data["response"])[:150]}')
    except Exception as e:
        print(f'  Raw: {r.data[:200]}')
else:
    print(f'  Body: {r.data[:300]}')

# Test POST /api/chat 
r2 = c.post('/api/chat', data=json.dumps({'message': 'What do you know?'}), content_type='application/json')
print(f'\nPOST /api/chat -> {r2.status_code}')
if r2.status_code == 200:
    try:
        data = r2.get_json()
        print(f'  Response keys: {list(data.keys()) if data else "None"}')
        if data and 'response' in data:
            print(f'  Response text: {str(data["response"])[:150]}')
    except Exception as e:
        print(f'  Raw: {r2.data[:200]}')
else:
    print(f'  Body: {r2.data[:300]}')

# Test knowledge search
r3 = c.get('/api/knowledge/search?q=consciousness')
print(f'\nGET /api/knowledge/search?q=consciousness -> {r3.status_code}')
if r3.status_code == 200:
    try:
        data = r3.get_json()
        print(f'  Results: {len(data.get("results", []))} found')
        for item in data.get('results', [])[:3]:
            print(f'    - {str(item.get("fact", item))[:80]}')
    except Exception as e:
        print(f'  Raw: {r3.data[:200]}')
else:
    print(f'  Body: {r3.data[:300]}')