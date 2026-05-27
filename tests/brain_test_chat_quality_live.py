"""Test what users actually experience when chatting with me."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
from web.app import create_app
NEW: """Test what users actually experience when chatting with me."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
from web.app import create_app

app = create_app()
client = app.test_client()

questions = [
    "What do you know about consciousness?",
    "Who are you?",
    "What have you learned recently?",
    "Help me understand what you can do",
]

for q in questions:
    r = client.post('/chat', json={'message': q}, content_type='application/json')
    print(f"\n{'='*60}")
    print(f"Q: {q}")
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.get_json()
        if data:
            resp = data.get('response', data.get('message', str(data)))
            # Truncate long responses
            if len(resp) > 300:
                resp = resp[:300] + '...'
            print(f"A: {resp}")
            if 'sources' in data:
                print(f"Sources: {data['sources']}")
        else:
            print(f"Raw: {r.data[:300]}")
    else:
        print(f"Error: {r.data[:200]}")