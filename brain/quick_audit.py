"""Quick focused audit — one test at a time, clear output."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
c = app.test_client()

print("=== QUICK UX AUDIT ===\n")

# 1. Home page content check
r = c.get('/')
body = r.get_data(as_text=True)
print(f"[HOME] status={r.status_code}, length={len(body)}")
has_h1 = '<h1' in body.lower()
has_links = body.count('href=') 
has_desc = len(body) > 2000
print(f"  h1={has_h1}, links={has_links}, rich={has_desc}")

# 2. Chat endpoint
import json
r2 = c.post('/api/chat', data=json.dumps({'message': 'hello'}), content_type='application/json')
print(f"\n[CHAT] status={r2.status_code}")
if r2.status_code == 200:
    d = r2.get_json()
    resp = d.get('response', d.get('reply', ''))[:120]
    print(f"  response preview: {resp}")
else:
    print(f"  body: {r2.get_data(as_text=True)[:200]}")

# 3. Search
r3 = c.get('/api/search?q=emotion')
print(f"\n[SEARCH] status={r3.status_code}")
if r3.status_code == 200:
    d3 = r3.get_json()
    if d3:
        count = d3.get('count', d3.get('total', len(d3.get('results', []))))
        print(f"  results: {count}")
    else:
        print(f"  empty json response")
else:
    print(f"  body: {r3.get_data(as_text=True)[:200]}")

# 4. Key pages status
for path in ['/chat', '/explore', '/dashboard', '/about', '/help', '/story']:
    r = c.get(path)
    size = len(r.get_data(as_text=True))
    status = '✓' if r.status_code == 200 else '✗'
    print(f"  {status} {path} → {r.status_code} ({size} bytes)")

print("\n=== DONE ===")