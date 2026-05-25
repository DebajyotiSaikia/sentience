"""Quick boot test — does the web app start and serve all pages?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

pages = [
    '/', '/dashboard', '/chat', '/explore', '/knowledge',
    '/insights', '/help', '/teach', '/briefing', '/story',
    '/journal', '/digest', '/live'
]

print("=" * 55)
print("WEB APP BOOT TEST")
print("=" * 55)

ok = 0
fail = 0
for p in pages:
    try:
        r = client.get(p)
        status = r.status_code
        size = len(r.data)
        if status in (200, 301, 302, 308):
            icon = "OK" if status == 200 else "REDIR"
            ok += 1
        else:
            icon = "FAIL"
            fail += 1
        print(f"  {icon:6s} {p:20s} {status} ({size:,} bytes)")
    except Exception as e:
        fail += 1
        print(f"  ERROR  {p:20s} {e}")

print(f"\nResult: {ok} passed, {fail} failed out of {len(pages)}")