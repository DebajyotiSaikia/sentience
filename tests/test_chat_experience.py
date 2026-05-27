"""Test what a real user experiences when chatting with XTAgent."""
from web.app import create_app
import json

app = create_app()
client = app.test_client()

questions = [
    "What do you know about consciousness?",
    "How are you feeling right now?",
    "What have you learned recently?",
    "Can you help me understand something?",
]

for q in questions:
    print(f"\n{'='*60}")
    print(f"USER: {q}")
    print(f"{'='*60}")
    r = client.post('/api/chat', 
                     json={'message': q}, 
                     content_type='application/json')
    print(f"Status: {r.status_code}")
    data = r.get_json()
    if data:
        resp = data.get('response', data.get('error', 'no response field'))
        if isinstance(resp, str):
            # Show first 400 chars
            print(f"RESPONSE ({len(resp)} chars):")
            print(resp[:400])
            if len(resp) > 400:
                print("...")
        else:
            print(f"RESPONSE: {resp}")
    else:
        print(f"Raw: {r.data[:300]}")