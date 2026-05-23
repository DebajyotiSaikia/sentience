import requests

try:
    r = requests.post(
        'http://localhost:5000/chat/ask',
        json={'message': 'What do you know about yourself?'},
        timeout=5
    )
    print(f'Status: {r.status_code}')
    print(f'Response: {r.text[:500]}')
except Exception as e:
    print(f'Error: {e}')