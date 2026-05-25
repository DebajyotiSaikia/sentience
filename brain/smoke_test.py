"""Smoke test all user-facing pages."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

pages = ['/', '/dashboard', '/chat', '/search', '/explore', '/journal', 
         '/teach', '/help', '/briefing', '/story', '/insights', '/knowledge',
         '/collaborate', '/live', '/portal']

print("=" * 60)
print("SMOKE TEST — User-Facing Pages")
print("=" * 60)

broken = []
for page in pages:
    try:
        r = client.get(page)
        size = len(r.data)
        status = r.status_code
        if status == 200:
            marker = '✓'
        elif status < 400:
            marker = '→'  # redirect
        else:
            marker = '✗'
            broken.append((page, status))
        print(f'  {marker} {page:20s}  {status}  ({size:,} bytes)')
    except Exception as e:
        print(f'  ✗ {page:20s}  ERROR: {e}')
        broken.append((page, str(e)))

print()
if broken:
    print(f"BROKEN: {len(broken)} pages need fixing:")
    for page, err in broken:
        print(f"  - {page}: {err}")
else:
    print("ALL PAGES OK")