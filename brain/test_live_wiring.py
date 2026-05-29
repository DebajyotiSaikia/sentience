"""Quick live endpoint test for chat wiring."""
import sys
sys.path.insert(0, '/workspace')

try:
    import requests
    r = requests.post(
        'http://localhost:8080/chat/ask',
        json={'message': 'What are you thinking about right now?'},
        timeout=15
    )
    print(f'Status: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        resp = data.get('response', '')
        print(f'Response length: {len(resp)}')
        print(f'Response preview: {resp[:400]}')
    else:
        print(f'Error: {r.text[:200]}')
except requests.exceptions.ConnectionError:
    print('Server not running — skip live test (OK)')
except Exception as e:
    print(f'Error: {e}')