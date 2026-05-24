import requests

endpoints = [
    'http://localhost:8501/knowledge/api/stats',
    'http://localhost:8501/knowledge/api/search?q=dream',
    'http://localhost:8501/knowledge/query',
    'http://localhost:8501/knowledge/',
]

for url in endpoints:
    try:
        r = requests.get(url, timeout=3)
        print(f'{r.status_code} {url}')
        if r.status_code == 200 and 'api' in url:
            print(f'  -> {r.text[:200]}')
    except Exception as e:
        print(f'FAIL {url}: {e}')