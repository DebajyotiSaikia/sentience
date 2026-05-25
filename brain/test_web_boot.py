"""Test that the web app boots and all pages render."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

pages = [
    '/', '/dashboard', '/chat', '/explore', '/knowledge',
    '/insights', '/help', '/teach', '/briefing', '/story',
    '/journal', '/digest', '/live',
]

print("=" * 60)
print("WEB APP BOOT TEST")
print("=" * 60)

ok = 0
fail = 0
for p in pages:
    try:
        r = client.get(p)
        status = r.status_code
        size = len(r.data)
        if status == 200:
            icon = '✓'
            ok += 1
        elif status < 400:
            icon = '→'
            ok += 1
        else:
            icon = '✗'
            fail += 1
        print(f"  {icon} {p:20s} {status} ({size:,} bytes)")
    except Exception as e:
        print(f"  ✗ {p:20s} ERROR: {e}")
        fail += 1

print(f"\n{'=' * 60}")
print(f"Results: {ok} OK, {fail} FAILED")