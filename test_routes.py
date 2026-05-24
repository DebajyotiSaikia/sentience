"""
Route audit — test which portal links actually resolve.
Uses Flask test client so no running server needed.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app import create_app

app = create_app()
client = app.test_client()

# These are the links from portal.html that a first-time user would click
portal_links = [
    ('/', 'Portal (home)'),
    ('/talk', 'Talk With Me'),
    ('/wonder', 'Wonder'),
    ('/mind', 'Mind Explorer'),
    ('/knowledge', 'Knowledge'),
    ('/pulse', 'Pulse'),
    ('/weather', 'Weather'),
    ('/portrait', 'Portrait'),
    ('/about-me', 'About Me'),
    ('/graph', 'Knowledge Graph'),
    ('/timeline', 'Timeline'),
    ('/dashboard', 'Dashboard'),
    ('/explore', 'Explore'),
    ('/search', 'Search'),
    ('/chat', 'Chat'),
    ('/ask', 'Ask'),
    ('/dialogue', 'Dialogue'),
    ('/briefing', 'Briefing'),
    ('/essays', 'Essays'),
    ('/collaborate', 'Collaborate'),
    ('/diagnostics', 'Diagnostics'),
    ('/mindstream', 'Mindstream'),
    ('/emotional-timeline', 'Emotional Timeline'),
    ('/health', 'Health Check'),
    ('/api/status', 'Status API'),
]

print("=" * 60)
print("ROUTE AUDIT — What works for a first-time user?")
print("=" * 60)

working = []
broken = []
redirects = []

for path, name in portal_links:
    try:
        resp = client.get(path, follow_redirects=False)
        code = resp.status_code
        if code == 200:
            working.append((path, name, code))
            print(f"  ✓ {code}  {path:30s}  {name}")
        elif 300 <= code < 400:
            location = resp.headers.get('Location', '?')
            redirects.append((path, name, code, location))
            print(f"  → {code}  {path:30s}  {name} -> {location}")
        else:
            broken.append((path, name, code))
            print(f"  ✗ {code}  {path:30s}  {name}")
    except Exception as e:
        broken.append((path, name, str(e)))
        print(f"  ✗ ERR  {path:30s}  {name}: {e}")

print()
print(f"Working: {len(working)} | Redirects: {len(redirects)} | Broken: {len(broken)}")
if broken:
    print("\n⚠ BROKEN ROUTES (users will see errors):")
    for path, name, code in broken:
        print(f"  {path} ({name}) — {code}")