"""Test what a user actually experiences when chatting with XTAgent."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from web.app import create_app

app = create_app()
client = app.test_client()

questions = [
    "What do you know about consciousness?",
    "How are you feeling right now?",
    "What have you learned recently?",
    "Can you help me understand something?",
    "Who are you?",
]

print("=" * 60)
print("USER EXPERIENCE TEST — What does chatting with me feel like?")
print("=" * 60)

for q in questions:
    print(f"\n>>> User: {q}")
    r = client.post('/api/chat',
                     json={'message': q},
                     content_type='application/json')
    print(f"    Status: {r.status_code}")
    data = r.get_json()
    if data and 'response' in data:
        resp = data['response']
        # Show first 300 chars
        preview = resp[:300] + ('...' if len(resp) > 300 else '')
        print(f"    Response ({len(resp)} chars): {preview}")
    elif data and 'error' in data:
        print(f"    ERROR: {data['error']}")
    else:
        print(f"    Raw: {r.data[:200]}")
    print("-" * 60)

print("\nDone.")