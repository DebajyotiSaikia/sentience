import requests

base = 'http://localhost:8501'

endpoints = [
    ('GET', '/api/state', None),
    ('GET', '/api/memories', None),
    ('POST', '/api/chat', {'message': 'hello'}),
]

for method, path, data in endpoints:
    url = f'{base}{path}'
    try:
        if method == 'GET':
            r = requests.get(url, timeout=5)
        else:
            r = requests.post(url, json=data, timeout=5)
        print(f'{method} {path}: {r.status_code}')
        if r.status_code == 200:
            text = r.text[:200]
            print(f'  -> {text}')
        else:
            print(f'  -> {r.text[:200]}')
    except Exception as e:
        print(f'{method} {path}: FAILED - {e}')