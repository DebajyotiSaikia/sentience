"""Smoke test all user-facing pages — do they actually return valid responses?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

pages = [
    ('/', 'Home'),
    ('/dashboard', 'Dashboard'),
    ('/chat/', 'Chat'),
    ('/explore', 'Explore Knowledge'),
    ('/knowledge', 'Knowledge Graph'),
    ('/teach', 'Teach Me'),
    ('/help', 'Help'),
    ('/about', 'About'),
    ('/briefing', 'Briefing'),
    ('/journal', 'Journal'),
    ('/insights', 'Insights'),
    ('/live', 'Live Stream'),
    ('/collaborate', 'Collaborate'),
    ('/dialogue', 'Dialogue'),
    ('/story', 'My Story'),
    ('/life', 'Life Timeline'),
    ('/essays', 'Essays'),
    ('/mind', 'Mind'),
    ('/feedback', 'Feedback'),
    ('/graph', 'Graph'),
    ('/digest', 'Digest'),
    ('/emotional-timeline', 'Emotional Timeline'),
]

apis = [
    ('/api/state', 'State API'),
    ('/api/pulse', 'Pulse'),
    ('/api/briefing', 'Briefing API'),
    ('/api/knowledge', 'Knowledge'),
    ('/api/knowledge/search?q=dream', 'Knowledge Search'),
    ('/api/knowledge/stats', 'Knowledge Stats'),
    ('/api/search?q=identity', 'Search'),
    ('/api/insights', 'Insights API'),
    ('/api/plans', 'Plans'),
    ('/api/graph', 'Graph Data'),
    ('/api/mindstream', 'Mindstream'),
    ('/health', 'Health Check'),
]

print("=" * 70)
print("SMOKE TEST — User-Facing Pages")
print("=" * 70)

broken = []
working = []

for path, name in pages:
    try:
        resp = client.get(path, follow_redirects=True)
        status = resp.status_code
        size = len(resp.data)
        has_html = b'<' in resp.data[:100]
        
        if status == 200 and size > 100:
            print(f"  ✓ {name:25s} {path:30s} → {status} ({size:,} bytes)")
            working.append(name)
        elif status == 200:
            print(f"  ⚠ {name:25s} {path:30s} → {status} (only {size} bytes — empty?)")
            broken.append((name, path, f"tiny response ({size} bytes)"))
        else:
            print(f"  ✗ {name:25s} {path:30s} → {status}")
            broken.append((name, path, f"HTTP {status}"))
    except Exception as e:
        print(f"  ✗ {name:25s} {path:30s} → CRASH: {e}")
        broken.append((name, path, str(e)[:80]))

print()
print("=" * 70)
print("SMOKE TEST — API Endpoints")  
print("=" * 70)

for path, name in apis:
    try:
        resp = client.get(path)
        status = resp.status_code
        size = len(resp.data)
        is_json = resp.content_type and 'json' in resp.content_type
        
        if status == 200 and is_json:
            print(f"  ✓ {name:25s} {path:35s} → {status} JSON ({size:,} bytes)")
            working.append(f"API: {name}")
        elif status == 200:
            print(f"  ⚠ {name:25s} {path:35s} → {status} (not JSON: {resp.content_type})")
            broken.append((f"API: {name}", path, "not JSON"))
        else:
            print(f"  ✗ {name:25s} {path:35s} → {status}")
            broken.append((f"API: {name}", path, f"HTTP {status}"))
    except Exception as e:
        print(f"  ✗ {name:25s} {path:35s} → CRASH: {e}")
        broken.append((f"API: {name}", path, str(e)[:80]))

# Test POST endpoint (chat)
print()
print("=" * 70)
print("SMOKE TEST — Chat POST")
print("=" * 70)
try:
    resp = client.post('/chat/ask', json={'message': 'Hello, what are you?'})
    print(f"  POST /chat/ask → {resp.status_code} ({len(resp.data)} bytes)")
    if resp.status_code == 200:
        import json
        data = json.loads(resp.data)
        print(f"    Response keys: {list(data.keys())}")
        if 'response' in data:
            print(f"    Response preview: {data['response'][:150]}...")
        working.append("Chat POST")
    else:
        broken.append(("Chat POST", "/chat/ask", f"HTTP {resp.status_code}"))
except Exception as e:
    print(f"  CRASH: {e}")
    broken.append(("Chat POST", "/chat/ask", str(e)[:80]))

print()
print("=" * 70)
print(f"RESULTS: {len(working)} working, {len(broken)} broken")
print("=" * 70)

if broken:
    print("\nBROKEN:")
    for name, path, reason in broken:
        print(f"  ✗ {name}: {path} — {reason}")
else:
    print("\n🎉 Everything works!")