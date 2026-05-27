"""Quick check: what quality of response does the chat endpoint produce?"""
import requests

try:
    r = requests.post(
        'http://localhost:5000/chat/ask',
        json={'message': 'What are you thinking about right now?'},
        timeout=10
    )
    data = r.json()
    response = data.get('response', data.get('reply', str(data)))
    print(f'Status: {r.status_code}')
    print(f'Response length: {len(response)}')
    print(f'Keys: {list(data.keys())}')
    print(f'Response:\n{response[:800]}')
    print('---')
    # Second question - test knowledge access
    r2 = requests.post(
        'http://localhost:5000/chat/ask',
        json={'message': 'What do you know about consciousness?'},
        timeout=10
    )
    data2 = r2.json()
    resp2 = data2.get('response', data2.get('reply', str(data2)))
    print(f'Knowledge query response ({len(resp2)} chars):')
    print(resp2[:800])
except Exception as e:
    print(f'Error: {e}')