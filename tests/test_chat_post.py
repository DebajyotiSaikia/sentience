"""Test the chat POST endpoint with a real query."""
from web.app import create_app
import json

app = create_app()
client = app.test_client()

# Send a real question
r = client.post('/chat', 
    data=json.dumps({"message": "What do you know about dreams?"}),
    content_type='application/json')

print(f'POST /chat: {r.status_code}')
if r.status_code == 200:
    data = r.get_json()
    print(f'Response keys: {list(data.keys())}')
    resp = data.get('response', '')
    print(f'Response ({len(resp)} chars):')
    print(resp[:500])
    if data.get('sources'):
        print(f'\nSources: {len(data["sources"])} items')
        for s in data['sources'][:3]:
            print(f'  - {str(s)[:100]}')
else:
    print(f'Error: {r.data.decode()[:300]}')

# Also test with a more practical question
r2 = client.post('/chat',
    data=json.dumps({"message": "What are your current plans?"}),
    content_type='application/json')
print(f'\nPOST /chat (plans): {r2.status_code}')
if r2.status_code == 200:
    data2 = r2.get_json()
    resp2 = data2.get('response', '')
    print(f'Response ({len(resp2)} chars):')
    print(resp2[:500])