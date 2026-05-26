"""Test: does the chat API produce genuinely useful responses?"""
import sys, os
sys.path.insert(0, '.')
from web.app import create_app

app = create_app()
client = app.test_client()

questions = [
    "What do you know about consciousness?",
    "What are you?",
    "What have you learned recently?",
]

for q in questions:
    r = client.post('/api/chat', json={'message': q}, content_type='application/json')
    print(f"\n{'='*60}")
    print(f"Q: {q}")
    print(f"Status: {r.status_code}")
    data = r.get_json()
    if data:
        resp = data.get('response', data.get('reply', data.get('error', 'no response key')))
        print(f"Response ({len(str(resp))} chars):")
        print(str(resp)[:400])
    else:
        print("No JSON response")
        print(r.data[:200])