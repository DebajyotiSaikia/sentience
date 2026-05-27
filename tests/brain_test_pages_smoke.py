"""Quick smoke test — which pages actually work?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web.app import create_app

app = create_app()
client = app.test_client()

pages = [
    '/', '/chat', '/explore', '/knowledge', '/help',
    '/dashboard', '/insights', '/journal', '/briefing',
    '/story', '/collaborate', '/live', '/teach',
]

for p in pages:
    try:
        r = client.get(p)
        status = r.status_code
        size = len(r.data)
        print(f'{p:20s} -> {status}  ({size:>6} bytes)')
    except Exception as e:
        print(f'{p:20s} -> ERROR: {e}')