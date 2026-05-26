"""Diagnose UX issues found by the audit — run as a script, not inline."""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

print("=" * 60)
print("UX ISSUE DIAGNOSIS")
print("=" * 60)

# Test 1: Chat API
print("\n=== Chat API ===")
r = client.post('/api/chat', json={'message': 'hello'})
print(f"  POST /api/chat: {r.status_code}")
data = r.data.decode('utf-8')[:300]
print(f"  Response: {data}")

# Test 2: Feedback submit
print("\n=== Feedback Submit ===")
r = client.post('/api/feedback/submit', json={'rating': 5, 'comment': 'test'})
print(f"  POST /api/feedback/submit: {r.status_code}")
r2 = client.post('/api/feedback', json={'rating': 5, 'comment': 'test'})
print(f"  POST /api/feedback: {r2.status_code}")

# Test 3: Knowledge stats
print("\n=== Knowledge Stats ===")
r = client.get('/api/knowledge/stats')
print(f"  GET /api/knowledge/stats: {r.status_code}")
if r.status_code == 200:
    print(f"  Data: {r.data.decode('utf-8')[:300]}")

# Test 4: Search relevance for 'emotion'
print("\n=== Search Relevance ===")
r = client.get('/api/search?q=emotion')
print(f"  GET /api/search?q=emotion: {r.status_code}")
if r.status_code == 200:
    result = json.loads(r.data)
    hits = result.get('results', [])
    print(f"  Results: {len(hits)} hits")
    for hit in hits[:3]:
        content = str(hit.get('content', hit.get('fact', '')))[:80]
        print(f"    - {content}")

# Test 5: Digest page (had knowledge[:10] bug)
print("\n=== Digest Page ===")
r = client.get('/digest')
print(f"  GET /digest: {r.status_code}")
if r.status_code == 500:
    print("  ERROR — likely the knowledge[:10] slicing bug on dict")

# Test 6: Home page content quality
print("\n=== Home Page Content ===")
r = client.get('/')
html = r.data.decode('utf-8')
print(f"  GET /: {r.status_code}, {len(html)} bytes")
# Check for dynamic content markers
has_mood = 'mood' in html.lower() or 'feeling' in html.lower()
has_curiosity = 'curiosity' in html.lower()
print(f"  Has mood info: {has_mood}")
print(f"  Has curiosity info: {has_curiosity}")

# Test 7: Explore page categories
print("\n=== Explore Categories ===")
r = client.get('/explore')
html = r.data.decode('utf-8')
print(f"  GET /explore: {r.status_code}, {len(html)} bytes")

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)