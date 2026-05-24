import urllib.request, urllib.error, json

req = urllib.request.Request(
    'http://localhost:8501/chat/ask',
    data=json.dumps({'query': 'Who are you?'}).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
try:
    resp = urllib.request.urlopen(req, timeout=15)
    print('Status:', resp.status)
    print(resp.read().decode()[:2000])
except urllib.error.HTTPError as e:
    print('HTTP Error:', e.code)
    print(e.read().decode()[:1000])
except Exception as e:
    print('Error:', type(e).__name__, e)