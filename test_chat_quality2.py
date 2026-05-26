"""Test what chat actually returns — is it genuinely useful?"""
from web.app import create_app
import json

app = create_app()
client = app.test_client()

questions = [
    "What do you know about consciousness?",
    "What are you?",
    "What have you learned recently?",
    "Can you help me understand your knowledge graph?",
]

for q in questions:
    r = client.post('/api/chat', 
                    data=json.dumps({'message': q}),
                    content_type='application/json')
    print(f"\nQ: {q}")
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = json.loads(r.data)
        resp = data.get('response', data.get('reply', str(data)))
        # Show first 300 chars
        print(f"A: {resp[:300]}")
        print(f"   [length: {len(resp)} chars]")
    else:
        print(f"Error: {r.data.decode()[:200]}")