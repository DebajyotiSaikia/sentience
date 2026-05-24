import requests

endpoints = ['/api/status', '/api/knowledge', '/api/memories', '/api/graph', '/api/plans']
for ep in endpoints:
    try:
        r = requests.get(f'http://localhost:8501{ep}', timeout=3)
        body = str(r.text)[:150]
        print(f'{ep}: {r.status_code} — {body}')
    except Exception as e:
        print(f'{ep}: FAILED — {e}')