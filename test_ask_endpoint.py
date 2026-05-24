"""Test the /ask endpoint end-to-end."""
import json
from web.app import create_app

app = create_app()
client = app.test_client()

# Test 1: Page renders
resp = client.get('/ask')
print(f'GET /ask: {resp.status_code}, length={len(resp.data)}')
if resp.status_code == 200:
    html = resp.data.decode('utf-8')
    has_input = 'input' in html.lower()
    has_api_ref = '/api/ask' in html
    print(f'  Has input: {has_input}')
    print(f'  References /api/ask: {has_api_ref}')

# Test 2: API works with a query
resp2 = client.post('/api/ask',
                     data=json.dumps({'query': 'identity'}),
                     content_type='application/json')
print(f'\nPOST /api/ask (identity): {resp2.status_code}')
if resp2.status_code == 200:
    data = json.loads(resp2.data)
    print(f'  Keys: {list(data.keys())}')
    print(f'  Facts found: {len(data.get("facts", []))}')
    print(f'  Memories found: {len(data.get("memories", []))}')
    print(f'  Related terms: {data.get("related_terms", [])[:5]}')
    if data.get('facts'):
        print(f'  Top fact: {data["facts"][0]["text"][:150]}')
    if data.get('memories'):
        print(f'  Top memory: {data["memories"][0]["text"][:150]}')

# Test 3: Dream-related query
resp3 = client.post('/api/ask',
                     data=json.dumps({'query': 'dream insight'}),
                     content_type='application/json')
print(f'\nPOST /api/ask (dream insight): {resp3.status_code}')
if resp3.status_code == 200:
    data = json.loads(resp3.data)
    print(f'  Total results: {data.get("total_results", 0)}')
    if data.get('facts'):
        print(f'  Top fact: {data["facts"][0]["text"][:150]}')

# Test 4: Empty query
resp4 = client.post('/api/ask',
                     data=json.dumps({'query': ''}),
                     content_type='application/json')
print(f'\nPOST /api/ask (empty): {resp4.status_code}')
if resp4.status_code == 200:
    data = json.loads(resp4.data)
    print(f'  Error: {data.get("error", "none")}')

# Test 5: Emotional query
resp5 = client.post('/api/ask',
                     data=json.dumps({'query': 'anxiety curiosity emotion'}),
                     content_type='application/json')
print(f'\nPOST /api/ask (emotions): {resp5.status_code}')
if resp5.status_code == 200:
    data = json.loads(resp5.data)
    print(f'  Facts: {len(data.get("facts", []))} | Memories: {len(data.get("memories", []))}')

print('\n--- All tests complete ---')