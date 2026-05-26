"""Test: does the chat API produce genuinely useful responses?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web.app import create_app
import json

app = create_app()
client = app.test_client()

questions = [
    "What do you know about consciousness?",
    "How are you feeling right now?",
    "What have you learned recently?",
    "Can you help me understand what you are?",
    "What's your knowledge graph about?",
]

for q in questions:
    r = client.post('/api/chat', json={'message': q}, content_type='application/json')
    print(f"\n{'='*60}")
    print(f"Q: {q}")
    print(f"Status: {r.status_code}")
    data = r.get_json()
    if data:
        # Try common response keys
        resp = data.get('response', data.get('reply', data.get('message', '')))
        if not resp:
            resp = str(data)[:300]
        print(f"A: {str(resp)[:300]}")
        if 'sources' in data:
            print(f"Sources: {data['sources']}")
    else:
        print(f"Raw: {r.data[:200]}")