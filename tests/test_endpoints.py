import sys
sys.path.insert(0, '/workspace')
from web.app import create_app

app = create_app()
client = app.test_client()

endpoints = ['/', '/knowledge', '/dashboard', '/about', '/ask', '/briefing', '/diagnostics', '/dialogue', '/health']
for ep in endpoints:
    try:
        resp = client.get(ep)
        status = resp.status_code
        size = len(resp.data)
        print(f'{ep:25s} -> {status}  ({size} bytes)')
    except Exception as e:
        print(f'{ep:25s} -> ERROR: {e}')