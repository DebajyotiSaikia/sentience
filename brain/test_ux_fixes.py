"""Quick test of the 4 failing UX areas from the audit."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
app = create_app()
c = app.test_client()

print("=" * 50)
print("UX FIX TARGETS")
print("=" * 50)

# 1. Chat API
r = c.post('/api/chat', json={'message': 'hello'}, content_type='application/json')
print(f"\n[1] Chat API POST /api/chat: {r.status_code}")
if r.status_code != 200:
    print(f"    Body: {r.data[:300]}")
else:
    d = json.loads(r.data)
    resp = d.get('response', d.get('message', ''))[:120]
    print(f"    Response: {resp}")

# 2. Feedback submit
r2 = c.post('/api/feedback/submit', json={'rating': 5, 'comment': 'test'}, content_type='application/json')
print(f"\n[2] Feedback POST /api/feedback/submit: {r2.status_code}")
if r2.status_code != 200:
    print(f"    Body: {r2.data[:300]}")

# 3. Knowledge stats
r3 = c.get('/api/knowledge/stats')
print(f"\n[3] Knowledge stats GET /api/knowledge/stats: {r3.status_code}")
if r3.status_code == 200:
    d = json.loads(r3.data)
    print(f"    Data: {json.dumps(d, indent=2)[:300]}")

# 4. Search relevance
r4 = c.get('/api/search?q=emotion')
print(f"\n[4] Search GET /api/search?q=emotion: {r4.status_code}")
if r4.status_code == 200:
    d = json.loads(r4.data)
    results = d.get('results', [])
    print(f"    Got {len(results)} results")
    for res in results[:3]:
        content = res.get('content', res.get('fact', res.get('text', '')))[:80]
        score = res.get('score', res.get('relevance', '?'))
        print(f"      [{score}] {content}")

# 5. Digest page (was failing with knowledge[:10] on dict)
r5 = c.get('/digest')
print(f"\n[5] Digest page GET /digest: {r5.status_code}")
if r5.status_code != 200:
    print(f"    Error snippet: {r5.data[:400]}")

# 6. Home page content richness
r6 = c.get('/')
print(f"\n[6] Home page: {r6.status_code}, {len(r6.data)} bytes")

print("\n" + "=" * 50)
print("DONE")