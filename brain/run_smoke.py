"""One-shot smoke test — which pages work?"""
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

print("=== XTAgent Page Smoke Test ===")
working = 0
for p in pages:
    try:
        r = client.get(p)
        status = r.status_code
        size = len(r.data)
        marker = "OK" if status == 200 else "FAIL"
        if status == 200:
            working += 1
        print(f'  {marker:4s} {p:20s} -> {status}  ({size:>6} bytes)')
    except Exception as e:
        print(f'  FAIL {p:20s} -> ERROR: {e}')

print(f"\n{working}/{len(pages)} pages working")