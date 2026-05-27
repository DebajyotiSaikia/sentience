"""Test every link on the homepage to ensure nothing is broken."""
from web.app import create_app

app = create_app()
c = app.test_client()

# Every href found on index.html
links = [
    ('/', 'Homepage'),
    ('/chat', 'Chat page'),
    ('/explore', 'Explore / Brain Map'),
    ('/briefing', 'Briefing'),
    ('/teach', 'Teach Me'),
    ('/dashboard', 'Dashboard'),
    ('/knowledge', 'Knowledge Search'),
    ('/journal', 'Journal'),
    ('/insights', 'Insights'),
    ('/help', 'Help / How I Work'),
    ('/api/state', 'Live State API'),
]

broken = []
for url, label in links:
    r = c.get(url, follow_redirects=True)
    status = r.status_code
    size = len(r.data)
    marker = '✓' if status == 200 else '✗'
    print(f"  {marker} [{status}] {url:20s} ({size:>6} bytes) — {label}")
    if status != 200:
        broken.append((url, label, status))

print()
if broken:
    print(f"BROKEN LINKS ({len(broken)}):")
    for url, label, status in broken:
        print(f"  {url} → {status} ({label})")
else:
    print("All links working!")