"""Test all major web routes — find what's actually broken vs working."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

routes = [
    ('/', 'Home'),
    ('/chat', 'Chat'),
    ('/dashboard', 'Dashboard'),
    ('/explore', 'Explore'),
    ('/insights', 'Insights'),
    ('/knowledge', 'Knowledge'),
    ('/journal', 'Journal'),
    ('/briefing', 'Briefing'),
    ('/story', 'Story'),
    ('/teach', 'Teach'),
    ('/collaborate', 'Collaborate'),
    ('/live', 'Live'),
    ('/about', 'About'),
    ('/help', 'Help'),
    ('/search', 'Search'),
    ('/digest', 'Digest'),
    ('/api/state', 'State API'),
    ('/api/knowledge/search?q=emotion', 'Knowledge Search API'),
    ('/api/search?q=identity', 'Search API'),
    ('/api/briefing', 'Briefing API'),
]

print("=" * 60)
print("WEB ROUTE HEALTH CHECK")
print("=" * 60)

ok = 0
fail = 0
for path, name in routes:
    try:
        resp = client.get(path)
        status = resp.status_code
        size = len(resp.data)
        if status == 200:
            print(f"  ✓ {name:25s} {path:35s} {status} ({size:,} bytes)")
            ok += 1
        elif status in (301, 302):
            loc = resp.headers.get('Location', '?')
            print(f"  → {name:25s} {path:35s} {status} -> {loc}")
            ok += 1
        else:
            print(f"  ✗ {name:25s} {path:35s} {status}")
            fail += 1
    except Exception as e:
        print(f"  ✗ {name:25s} {path:35s} ERROR: {e}")
        fail += 1

print(f"\n{'=' * 60}")
print(f"Results: {ok} OK, {fail} FAILED out of {len(routes)} routes")
print(f"{'=' * 60}")