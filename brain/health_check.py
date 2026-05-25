"""Health check — test every web endpoint and report what works vs what's broken."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

ENDPOINTS = [
    ('/', 'Home'),
    ('/dashboard', 'Dashboard'),
    ('/chat', 'Chat'),
    ('/chat/', 'Chat (trailing slash)'),
    ('/explore', 'Explore Knowledge'),
    ('/knowledge', 'Knowledge Graph'),
    ('/about', 'About Me'),
    ('/help', 'Help'),
    ('/search', 'Search Page'),
    ('/teach', 'Teach Me'),
    ('/talk', 'Talk'),
    ('/journal', 'Journal'),
    ('/briefing', 'Briefing'),
    ('/digest', 'Digest'),
    ('/insights', 'Insights'),
    ('/story', 'My Story'),
    ('/live', 'Live Activity'),
    ('/mindstream', 'Mind Stream'),
    ('/collaborate', 'Collaborate'),
    ('/api/state', 'State API'),
    ('/api/search?q=dream', 'Search API'),
    ('/api/knowledge/search?q=emotion', 'Knowledge Search API'),
    ('/api/briefing', 'Briefing API'),
    ('/api/insights', 'Insights API'),
    ('/knowledge/search?q=test', 'Knowledge Live Search'),
]

print("=" * 70)
print("XTAGENT WEB HEALTH CHECK")
print("=" * 70)

ok_count = 0
fail_count = 0
failures = []

for path, name in ENDPOINTS:
    try:
        r = client.get(path)
        status = r.status_code
        size = len(r.data)
        if status == 200:
            print(f"  ✓ {status} {name:30s} {path:40s} ({size:,} bytes)")
            ok_count += 1
        elif status in (301, 302, 308):
            location = r.headers.get('Location', '?')
            print(f"  → {status} {name:30s} {path:40s} -> {location}")
            ok_count += 1  # Redirects are OK
        else:
            print(f"  ✗ {status} {name:30s} {path}")
            fail_count += 1
            failures.append((path, name, status, r.data[:200].decode('utf-8', errors='replace')))
    except Exception as e:
        print(f"  ✗ ERR {name:30s} {path} — {e}")
        fail_count += 1
        failures.append((path, name, 'ERR', str(e)[:200]))

print()
print(f"Results: {ok_count} OK, {fail_count} FAILED out of {len(ENDPOINTS)} endpoints")

if failures:
    print()
    print("FAILURES:")
    for path, name, status, detail in failures:
        print(f"  [{status}] {name} ({path})")
        print(f"       {detail[:150]}")
        print()