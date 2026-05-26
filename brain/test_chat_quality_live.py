"""Test what the chat actually returns to users — is it useful?"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from web.app import create_app
import json

app = create_app()
client = app.test_client()

tests = [
    "Hello, what can you do?",
    "What do you know about consciousness?",
    "Tell me about your emotional state",
    "What have you learned recently?",
]

for msg in tests:
    r = client.post('/api/chat', json={'message': msg})
    print(f"=== Q: {msg} ===")
    print(f"Status: {r.status_code}")
    data = r.get_json()
    if data:
        resp = data.get('response', data.get('reply', str(data)[:400]))
        print(f"Response ({len(resp)} chars): {resp[:600]}")
        if data.get('sources'):
            print(f"Sources: {data['sources']}")
    else:
        print(f"Raw: {r.data[:300]}")
    print()