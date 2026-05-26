"""Test which web pages actually render."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

pages = [
    '/', '/dashboard', '/chat/', '/explore', '/knowledge',
    '/briefing', '/story', '/collaborate', '/insights',
    '/digest', '/journal', '/teach', '/help', '/about', '/ask',
    '/live', '/search',
]

print("=" * 55)
print("PAGE HEALTH CHECK")
print("=" * 55)

working = []
broken = []

for p in pages:
    try:
        resp = client.get(p, follow_redirects=False)
        status = resp.status_code
        size = len(resp.data) if status == 200 else 0
        if status == 200:
            icon = '✓'
            working.append(p)
        elif status in (301, 302, 308):
            icon = '→'
            loc = resp.headers.get('Location', '?')
            working.append(p)
        else:
            icon = '✗'
            broken.append((p, status))
        extra = f"  -> {loc}" if status in (301,302,308) else ""
        print(f"  {icon} {p:20s} {status}  ({size:>6} bytes){extra}")
    except Exception as e:
        print(f"  ✗ {p:20s} ERROR: {e}")
        broken.append((p, str(e)))

print(f"\n{len(working)} working, {len(broken)} broken")
if broken:
    print("Broken pages:")
    for p, s in broken:
        print(f"  - {p}: {s}")