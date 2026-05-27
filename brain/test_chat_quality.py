"""Test chat response quality — what do users actually experience?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
import json

app = create_app()
client = app.test_client()

tests = [
    ("Greeting", "Hello, who are you?"),
    ("Knowledge", "What do you know about consciousness?"),
    ("Feeling", "How are you feeling right now?"),
    ("Plans", "What are your plans?"),
    ("Capability", "What can you do?"),
    ("Teaching", "The speed of light is 299,792,458 meters per second"),
]

for name, msg in tests:
    r = client.post('/chat/ask', json={'message': msg}, content_type='application/json')
    print(f"=== {name} ===")
    print(f"Status: {r.status_code}")
    d = r.get_json() if r.status_code == 200 else {}
    if d:
        resp = d.get('response', d.get('error', '?'))
        # Truncate for readability
        if len(resp) > 400:
            resp = resp[:400] + '...'
        print(f"Response: {resp}")
        # Show metadata if present
        for key in ['sources_used', 'knowledge_used', 'context_type']:
            if key in d:
                print(f"  {key}: {d[key]}")
    else:
        print(f"Raw: {r.data[:200]}")
    print()