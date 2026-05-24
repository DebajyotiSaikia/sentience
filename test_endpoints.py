import urllib.request

endpoints = ['/knowledge', '/ask', '/dialogue', '/chat', '/query', '/graph']
for ep in endpoints:
    try:
        r = urllib.request.urlopen(f'http://localhost:5000{ep}')
        print(f'{ep}: {r.status} OK ({len(r.read())} bytes)')
    except Exception as e:
        print(f'{ep}: ERROR - {e}')