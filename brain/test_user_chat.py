"""Test what users actually see when they chat with me."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web.app import create_app

app = create_app()
client = app.test_client()

queries = [
    'What do you know about consciousness?',
    'How are you feeling?',
    'What have you learned recently?',
    'Tell me about integrated information theory',
    'What are your goals?',
]

for q in queries:
    r = client.post('/chat/ask', json={'message': q}, content_type='application/json')
    data = r.get_json()
    resp = data.get('response', data.get('error', '???'))
    print(f'Q: {q}')
    print(f'A: {resp[:250]}')
    print('---')