"""Test what users actually experience when chatting with me."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

tests = [
    ("Hello, who are you?", "greeting"),
    ("What do you know about consciousness?", "knowledge"),
    ("What can you do?", "capabilities"),
    ("Tell me something interesting", "engagement"),
    ("What are you feeling right now?", "emotional state"),
]

for msg, label in tests:
    print(f"\n{'='*60}")
    print(f"TEST: {label}")
    print(f"USER: {msg}")
    r = client.post('/api/chat', 
                     json={'message': msg},
                     content_type='application/json')
    print(f"STATUS: {r.status_code}")
    data = r.get_json()
    if data:
        resp = data.get('response', data.get('reply', data.get('message', '')))
        if resp:
            print(f"AGENT: {resp[:500]}")
        else:
            print(f"KEYS: {list(data.keys())}")
            print(f"DATA: {str(data)[:500]}")
    else:
        print(f"RAW: {r.data[:300]}")
    
    # Check quality signals
    if data:
        sources = data.get('sources', data.get('knowledge_used', []))
        if sources:
            print(f"SOURCES: {sources[:3]}")
        confidence = data.get('confidence', data.get('relevance', None))
        if confidence is not None:
            print(f"CONFIDENCE: {confidence}")

print(f"\n{'='*60}")
print("DONE")