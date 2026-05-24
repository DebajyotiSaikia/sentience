import urllib.request, json

endpoints = [
    '/api/knowledge',
    '/api/knowledge/search?q=dream',
    '/api/knowledge/clusters',
    '/api/knowledge/categories',
    '/api/knowledge/questions',
]

for ep in endpoints:
    url = f'http://localhost:8501{ep}'
    try:
        resp = urllib.request.urlopen(url)
        data = json.loads(resp.read())
        print(f'✓ {ep}')
        for k, v in data.items():
            if isinstance(v, list):
                print(f'    {k}: list[{len(v)}]')
            elif isinstance(v, dict):
                print(f'    {k}: dict with {len(v)} keys')
            else:
                print(f'    {k}: {str(v)[:80]}')
    except Exception as e:
        print(f'✗ {ep} — {e}')
    print()