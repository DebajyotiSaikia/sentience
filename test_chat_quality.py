"""Test the chat endpoint — the primary user interaction point."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app import create_app

app = create_app()
client = app.test_client()

questions = [
    "What do you know about yourself?",
    "What are you currently working on?",
    "Can you help me understand something?",
]

for q in questions:
    print(f"\n{'='*60}")
    print(f"Q: {q}")
    r = client.post('/chat/send', json={'message': q})
    print(f"Status: {r.status_code}")
    try:
        data = json.loads(r.data)
        if 'response' in data:
            resp = data['response']
            print(f"Response ({len(resp)} chars):")
            print(resp[:500])
        if 'error' in data:
            print(f"Error: {data['error']}")
        if 'knowledge_used' in data:
            print(f"Knowledge hits: {data['knowledge_used']}")
    except Exception as e:
        print(f"Parse error: {e}")
        print(f"Raw: {r.data[:200]}")