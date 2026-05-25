"""Quick test: does the web app boot and serve all pages?"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web.app import create_app

app = create_app()
client = app.test_client()

pages = [
    '/', '/dashboard', '/chat', '/briefing', '/explore',
    '/search', '/help', '/knowledge', '/insights',
    '/journal', '/teach', '/talk',
]

print("Web App Boot Test")
print("=" * 50)
ok = 0
fail = 0
for page in pages:
    try:
        resp = client.get(page)
        status = resp.status_code
        size = len(resp.data)
        icon = '✓' if status == 200 else '→' if status < 400 else '✗'
        print(f"  {icon} {page:20s} {status}  ({size:,} bytes)")
        if status == 200:
            ok += 1
        else:
            fail += 1
    except Exception as e:
        print(f"  ✗ {page:20s} ERROR: {e}")
        fail += 1

print(f"\n{ok} ok, {fail} issues")