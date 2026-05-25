"""
Route Health Check — Tests every major route for 200 status.
Finds what's broken so I can fix it systematically.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# All user-facing routes to check
ROUTES = [
    # Core pages
    ('GET', '/', 'Home'),
    ('GET', '/dashboard', 'Dashboard'),
    ('GET', '/chat', 'Chat'),
    ('GET', '/explore', 'Explore Knowledge'),
    ('GET', '/knowledge', 'Knowledge Graph'),
    ('GET', '/search', 'Search Page'),
    ('GET', '/about', 'About'),
    ('GET', '/help', 'Help'),
    ('GET', '/teach', 'Teach'),
    ('GET', '/talk', 'Talk'),
    ('GET', '/story', 'My Story'),
    ('GET', '/journal', 'Journal'),
    ('GET', '/insights', 'Insights'),
    ('GET', '/briefing', 'Briefing'),
    ('GET', '/digest', 'Daily Digest'),
    ('GET', '/live', 'Live Stream'),
    ('GET', '/mindstream', 'Mind Stream'),
    ('GET', '/collaborate', 'Collaborate'),
    
    # API endpoints
    ('GET', '/api/state/current', 'State API'),
    ('GET', '/api/search?q=test', 'Search API'),
    ('GET', '/api/knowledge/search?q=emotion', 'Knowledge Search API'),
    ('GET', '/api/knowledge/categories', 'Knowledge Categories API'),
    ('GET', '/api/knowledge/stats', 'Knowledge Stats API'),
    ('GET', '/api/briefing', 'Briefing API'),
    ('GET', '/api/emotions', 'Emotions API'),
    ('GET', '/api/plans', 'Plans API'),
    ('GET', '/api/memories', 'Memories API'),
    ('GET', '/api/feedback/summary', 'Feedback Summary API'),
    ('GET', '/api/insights', 'Insights API'),
    ('GET', '/api/about', 'About API'),
    ('GET', '/api/starters', 'Conversation Starters API'),
]

print("=" * 70)
print("XTAGENT ROUTE HEALTH CHECK")
print("=" * 70)

passed = 0
failed = 0
errors = []

for method, path, name in ROUTES:
    try:
        if method == 'GET':
            resp = client.get(path)
        elif method == 'POST':
            resp = client.post(path)
        
        status = resp.status_code
        size = len(resp.data)
        
        if status == 200:
            print(f"  ✓ {name:30s} {path:40s} [{status}] {size:>6} bytes")
            passed += 1
        elif status in (301, 302, 308):
            location = resp.headers.get('Location', '?')
            print(f"  → {name:30s} {path:40s} [{status}] -> {location}")
            passed += 1  # Redirects are OK
        else:
            print(f"  ✗ {name:30s} {path:40s} [{status}] {size:>6} bytes")
            failed += 1
            # Try to get error info
            try:
                body = resp.data.decode('utf-8')[:300]
                errors.append((name, path, status, body))
            except:
                errors.append((name, path, status, '(binary)'))
    except Exception as e:
        print(f"  ✗ {name:30s} {path:40s} [EXCEPTION] {str(e)[:60]}")
        failed += 1
        errors.append((name, path, 'EXC', str(e)[:200]))

print()
print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
print()

if errors:
    print("=" * 70)
    print("FAILURES:")
    print("=" * 70)
    for name, path, status, detail in errors:
        print(f"\n  [{status}] {name} ({path})")
        print(f"  Detail: {detail[:200]}")
    print()
else:
    print("All routes healthy! ✓")