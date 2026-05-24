import urllib.request, json

try:
    resp = urllib.request.urlopen('http://localhost:8501/api/knowledge/search?q=dream')
    data = json.loads(resp.read())
    print('Status:', resp.status)
    print('Results:', len(data.get('results', [])))
    for r in data.get('results', [])[:3]:
        print(' -', r.get('fact', r.get('text', str(r)))[:80])
except Exception as e:
    print(f'Error: {e}')

try:
    resp2 = urllib.request.urlopen('http://localhost:8501/api/knowledge/stats')
    data2 = json.loads(resp2.read())
    print('\nStats:', json.dumps(data2, indent=2)[:300])
except Exception as e:
    print(f'Stats error: {e}')