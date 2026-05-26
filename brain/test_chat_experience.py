"""Test what a user actually experiences when chatting with me."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# Test cases a real user would try
test_messages = [
    "What do you know about consciousness?",
    "Tell me about yourself",
    "What are you curious about right now?",
    "Can you help me understand something?",
    "What have you learned recently?",
]

print("=" * 70)
print("CHAT EXPERIENCE TEST — What do users actually get?")
print("=" * 70)

for msg in test_messages:
    print(f"\n>>> User: {msg}")
    r = client.post('/api/chat', 
                     json={'message': msg},
                     content_type='application/json')
    print(f"    Status: {r.status_code}")
    if r.status_code == 200:
        d = r.get_json()
        if d:
            response = d.get('response', d.get('message', ''))
            sources = d.get('sources', d.get('knowledge_used', []))
            print(f"    Response ({len(str(response))} chars):")
            # Show first 500 chars
            for line in str(response)[:500].split('\n'):
                print(f"      {line}")
            if sources:
                print(f"    Sources: {sources}")
            # Check quality signals
            has_knowledge = bool(sources) or 'know' in str(response).lower()
            is_generic = len(str(response)) < 50
            print(f"    Quality: {'GENERIC' if is_generic else 'OK'} | Knowledge: {'YES' if has_knowledge else 'NO'}")
        else:
            print(f"    Raw: {r.data[:300]}")
    else:
        print(f"    ERROR: {r.data[:200]}")

print("\n" + "=" * 70)
print("DIAGNOSIS")
print("=" * 70)