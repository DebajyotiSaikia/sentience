"""Test ALL nav links — find broken ones."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

nav_pages = [
    '/', '/chat', '/explore', '/knowledge', '/insights',
    '/journal', '/story', '/collaborate', '/live', '/teach',
    '/briefing', '/help', '/about', '/dashboard',
]

broken = []
print("=== ALL NAV PAGES ===")
for p in nav_pages:
    try:
        r = client.get(p)
        status = r.status_code
        size = len(r.data)
        marker = " *** BROKEN ***" if status >= 400 else ""
        print(f"  {p:20s} -> {status}  ({size:>6} bytes){marker}")
        if status >= 400:
            broken.append(p)
    except Exception as e:
        print(f"  {p:20s} -> ERROR: {e}")
        broken.append(p)

print(f"\n{'='*40}")
if broken:
    print(f"BROKEN PAGES ({len(broken)}): {', '.join(broken)}")
else:
    print("ALL PAGES WORKING!")