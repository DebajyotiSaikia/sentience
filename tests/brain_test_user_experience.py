"""Test what a real user sees — every main page should return 200 with real content."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# The pages from nav.js — what users actually click
PAGES = [
    ('/', 'Home'),
    ('/dashboard', 'Dashboard'),
    ('/chat/', 'Chat'),
    ('/search', 'Search'),
    ('/explore', 'Explore'),
    ('/journal', 'Journal'),
    ('/teach', 'Teach'),
    ('/help', 'Help'),
    ('/briefing', 'Briefing'),
    ('/knowledge', 'Knowledge'),
    ('/story', 'Story'),
    ('/insights', 'Insights'),
    ('/talk', 'Talk'),
    ('/collaborate/', 'Collaborate'),
    ('/about', 'About'),
]

# Key API endpoints users/frontend depend on
APIS = [
    ('/api/knowledge/stats', 'Knowledge Stats'),
    ('/api/knowledge/search?q=dream', 'Knowledge Search'),
    ('/api/state/emotions', 'Emotions API'),
    ('/api/live/state', 'Live State'),
    ('/api/briefing', 'Briefing API'),
    ('/api/insights', 'Insights API'),
    ('/api/search?q=identity', 'Search API'),
]

print("=" * 60)
print("USER EXPERIENCE TEST — What do visitors actually see?")
print("=" * 60)

failures = []

print("\n📄 PAGE TESTS:")
for path, name in PAGES:
    resp = client.get(path)
    status = resp.status_code
    # Follow redirects
    if status in (301, 302, 308):
        loc = resp.headers.get('Location', '?')
        resp = client.get(loc)
        status = resp.status_code
    
    size = len(resp.data)
    ok = status == 200 and size > 100
    marker = "✅" if ok else "❌"
    print(f"  {marker} {name:20s} {path:30s} → {status}  ({size:,} bytes)")
    if not ok:
        failures.append((name, path, status, size))
        # Show error snippet
        if status >= 400:
            snippet = resp.data.decode('utf-8', errors='replace')[:300]
            print(f"      Error: {snippet[:200]}")

print(f"\n🔌 API TESTS:")
for path, name in APIS:
    resp = client.get(path)
    status = resp.status_code
    size = len(resp.data)
    ok = status == 200
    marker = "✅" if ok else "❌"
    
    # Check it's valid JSON
    try:
        import json
        data = json.loads(resp.data)
        json_ok = True
    except:
        json_ok = False
    
    json_marker = "📦" if json_ok else "⚠️"
    print(f"  {marker} {name:20s} {path:35s} → {status}  {json_marker} ({size:,} bytes)")
    if not ok:
        failures.append((name, path, status, size))

print(f"\n{'=' * 60}")
if failures:
    print(f"❌ {len(failures)} FAILURES:")
    for name, path, status, size in failures:
        print(f"   • {name} ({path}) — status {status}, {size} bytes")
else:
    print("✅ ALL TESTS PASSED — Every page and API works!")
print(f"{'=' * 60}")