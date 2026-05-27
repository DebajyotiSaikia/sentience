"""Test chat response quality — does XTAgent give genuinely useful answers?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
import json

app = create_app()
client = app.test_client()

questions = [
    "What do you know about consciousness?",
    "What can you do?",
    "Tell me something interesting",
    "What have you learned recently?",
    "Who are you?",
]

for q in questions:
    r = client.post('/api/chat', json={'message': q}, content_type='application/json')
    print(f"=== Q: {q} ===")
    print(f"Status: {r.status_code}")
    try:
        data = json.loads(r.data)
        resp = data.get('response', str(data))
        print(f"Response ({len(resp)} chars): {resp[:400]}")
        if 'knowledge_used' in data:
            print(f"Knowledge used: {data['knowledge_used']}")
        if 'sources' in data:
            print(f"Sources: {data['sources']}")
    except Exception as e:
        print(f"Parse error: {e}")
        print(f"Raw: {r.data[:300]}")
    print()