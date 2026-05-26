"""Test what users actually experience when chatting with XTAgent."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
import json

app = create_app()
client = app.test_client()

questions = [
    'What do you know about consciousness?',
    'What can you do?',
    'Tell me about yourself',
    'What have you learned recently?',
]

for q in questions:
    r = client.post('/api/chat', json={'message': q}, content_type='application/json')
    data = r.get_json()
    response = data.get('response', data.get('error', 'NO RESPONSE'))
    # Show first 300 chars
    print(f'Q: {q}')
    print(f'A: {response[:300]}')
    print(f'Status: {r.status_code} | Length: {len(response)}')
    print('---')