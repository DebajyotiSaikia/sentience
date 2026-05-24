"""Quick test: which user-facing routes actually work?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app import create_app

app = create_app()
client = app.test_client()

routes_to_test = [
    '/', '/explore', '/search', '/ask', '/knowledge',
    '/mind', '/about-me', '/briefing', '/talk', '/wonder',
    '/pulse', '/dashboard', '/graph', '/reflect',
    '/api/status', '/health',
]

print(f"{'Route':<25} {'Status':<8} {'Size':<10} Notes")
print("-" * 60)
for route in routes_to_test:
    try:
        resp = client.get(route)
        size = len(resp.data)
        note = ''
        if resp.status_code == 302:
            note = f'-> {resp.headers.get("Location","?")}'
        elif resp.status_code == 200 and size < 100:
            note = resp.data[:80].decode(errors='replace')
        print(f"{route:<25} {resp.status_code:<8} {size:<10} {note}")
    except Exception as e:
        print(f"{route:<25} ERROR    -          {type(e).__name__}: {e}")