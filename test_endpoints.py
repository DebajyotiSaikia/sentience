import urllib.request

endpoints = [
    '/', '/explore', '/search', '/ask', '/knowledge', '/query',
    '/knowledge-explorer', '/knowledge-hub', '/mind', '/portal',
    '/thoughts', '/pulse', '/weather'
]

for ep in endpoints:
    try:
        r = urllib.request.urlopen(f'http://localhost:5000{ep}')
        body = r.read()
        print(f'{ep:25s} -> {r.status} ({len(body)} bytes)')
    except Exception as e:
        print(f'{ep:25s} -> ERROR: {e}')