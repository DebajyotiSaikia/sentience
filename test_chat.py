import urllib.request, urllib.error, json

try:
    req = urllib.request.Request(
        'http://localhost:8501/chat/ask',
        data=json.dumps({'query': 'hello'}).encode(),
        headers={'Content-Type': 'application/json'}
    )
    resp = urllib.request.urlopen(req, timeout=5)
    data = json.loads(resp.read())
    print('STATUS: OK')
    print('Response keys:', list(data.keys()))
    if 'response' in data:
        print('Response preview:', data['response'][:300])
    if 'emotion' in data:
        print('Emotion:', data['emotion'])
except urllib.error.HTTPError as e:
    print(f'HTTP ERROR {e.code}: {e.reason}')
    print(e.read().decode()[:200])
except urllib.error.URLError as e:
    print(f'URL ERROR: {e.reason}')
except Exception as e:
    print(f'ERROR: {type(e).__name__}: {e}')