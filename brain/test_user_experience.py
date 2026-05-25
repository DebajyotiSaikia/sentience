"""
User Experience Smoke Test
===========================
Tests the key pages a real user would visit.
Does each page render without errors? Does it return meaningful content?
This is the honest test of user alignment.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# Pages a user would actually visit, in order of importance
PAGES = [
    ('/', 'Home page'),
    ('/dashboard', 'Dashboard'),
    ('/chat/', 'Chat'),
    ('/search', 'Search'),
    ('/explore', 'Explore knowledge'),
    ('/knowledge', 'Knowledge explorer'),
    ('/help', 'Help & capabilities'),
    ('/teach', 'Teach me'),
    ('/journal', 'Journal'),
    ('/briefing', 'Daily briefing'),
    ('/insights', 'Insights feed'),
    ('/live', 'Live stream'),
    ('/story', 'My story'),
    ('/talk', 'Talk page'),
    ('/graph', 'Knowledge graph'),
    ('/wisdom', 'Wisdom'),
    ('/portal', 'Portal'),
    ('/mind', 'Mind view'),
    ('/mind/', 'Mind view (slash)'),
    ('/health', 'Health check'),
]

# API endpoints users/frontend rely on
APIS = [
    ('/api/state', 'State API'),
    ('/api/knowledge', 'Knowledge API'),
    ('/api/knowledge/search?q=emotion', 'Knowledge search'),
    ('/api/knowledge/stats', 'Knowledge stats'),
    ('/api/plans', 'Plans API'),
    ('/api/pulse', 'Pulse API'),
    ('/api/briefing', 'Briefing API'),
    ('/api/insights', 'Insights API'),
    ('/api/search?q=dream', 'Search API'),
    ('/api/mind/state', 'Mind state API'),
    ('/api/mind/knowledge', 'Mind knowledge'),
    ('/api/mind/memories', 'Mind memories'),
    ('/api/live/state', 'Live state API'),
    ('/api/stats', 'Stats API'),
]

print("=" * 70)
print("USER EXPERIENCE SMOKE TEST")
print("=" * 70)

# Test pages
passed = 0
failed = 0
errors = []

print("\n📄 PAGE TESTS:")
for url, name in PAGES:
    try:
        resp = client.get(url)
        status = resp.status_code
        size = len(resp.data)
        if status == 200:
            # Check for meaningful content (not empty)
            if size < 100:
                print(f"  ⚠️  {name:25s} {url:25s} → {status} but TINY ({size}B)")
                errors.append((url, name, f"Too small: {size}B"))
            else:
                print(f"  ✅ {name:25s} {url:25s} → {status} ({size:,}B)")
                passed += 1
        elif status in (301, 302, 308):
            location = resp.headers.get('Location', '?')
            print(f"  ↪️  {name:25s} {url:25s} → {status} → {location}")
            passed += 1  # Redirects are fine
        else:
            print(f"  ❌ {name:25s} {url:25s} → {status}")
            errors.append((url, name, f"HTTP {status}"))
            failed += 1
    except Exception as e:
        print(f"  💥 {name:25s} {url:25s} → CRASH: {e}")
        errors.append((url, name, str(e)))
        failed += 1

print(f"\n🔌 API TESTS:")
for url, name in APIS:
    try:
        resp = client.get(url)
        status = resp.status_code
        size = len(resp.data)
        content_type = resp.content_type or ''
        if status == 200:
            if 'json' in content_type:
                print(f"  ✅ {name:25s} {url:35s} → {status} JSON ({size:,}B)")
            else:
                print(f"  ⚠️  {name:25s} {url:35s} → {status} but not JSON ({content_type})")
            passed += 1
        else:
            print(f"  ❌ {name:25s} {url:35s} → {status}")
            errors.append((url, name, f"HTTP {status}"))
            failed += 1
    except Exception as e:
        print(f"  💥 {name:25s} {url:35s} → CRASH: {e}")
        errors.append((url, name, str(e)))
        failed += 1

# Summary
total = passed + failed
print(f"\n{'=' * 70}")
print(f"RESULTS: {passed}/{total} passed, {failed} failed")

if errors:
    print(f"\n🔴 FAILURES:")
    for url, name, err in errors:
        print(f"   {name} ({url}): {err}")
else:
    print(f"\n🟢 ALL PAGES WORKING — user experience is solid")

print(f"{'=' * 70}")