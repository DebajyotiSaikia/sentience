"""Diagnose the 8 UX audit failures to understand exact causes."""
import sys, os, json, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

print("=" * 60)
print("DIAGNOSING UX FAILURES")
print("=" * 60)

# 1. Chat API
print("\n[1] Chat API...")
try:
    resp = client.post('/api/chat',
                       json={'message': 'Hello, what are you?'},
                       content_type='application/json')
    print(f"  Status: {resp.status_code}")
    print(f"  Body: {resp.data[:300].decode()}")
except Exception as e:
    print(f"  ERROR: {e}")
    traceback.print_exc()

# 2. Search relevance
print("\n[2] Search relevance...")
for query in ['emotion', 'identity', 'dream']:
    resp = client.get(f'/api/search?q={query}&limit=3')
    data = resp.get_json() if resp.status_code == 200 else {}
    results = data.get('results', [])
    print(f"  '{query}': {len(results)} results")
    for r in results[:2]:
        content = str(r.get('content', r.get('fact', r.get('text', '?'))))[:100]
        print(f"    -> {content}")

# 3. Knowledge stats (reports 0 facts)
print("\n[3] Knowledge stats...")
resp = client.get('/api/knowledge/stats')
print(f"  Status: {resp.status_code}")
if resp.status_code == 200:
    print(f"  Data: {resp.data[:300].decode()}")

# 4. Feedback submit
print("\n[4] Feedback submit...")
resp = client.post('/api/feedback',
                   json={'rating': 5, 'comment': 'test'},
                   content_type='application/json')
print(f"  Status: {resp.status_code}")
print(f"  Body: {resp.data[:200].decode()}")

# 5. Home page links & CTA
print("\n[5] Home page analysis...")
resp = client.get('/')
html = resp.data.decode()
import re
links = re.findall(r'href=["\']([^"\']+)["\']', html)
internal = [l for l in links if l.startswith('/')]
print(f"  Internal links: {len(internal)}")
for l in internal[:10]:
    print(f"    {l}")
cta_patterns = ['chat', 'talk', 'try', 'start', 'ask', 'explore', 'begin']
cta_found = [p for p in cta_patterns if p in html.lower()]
print(f"  CTA words found: {cta_found}")

# 6. Check knowledge.json location and content
print("\n[6] Knowledge data files...")
for path in ['brain/knowledge.json', 'persist/knowledge_graph.json', 'persist/knowledge.json']:
    full = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), path)
    if os.path.exists(full):
        with open(full) as f:
            data = json.load(f)
        if isinstance(data, dict):
            keys = list(data.keys())[:5]
            if 'nodes' in data:
                print(f"  {path}: graph format, {len(data.get('nodes', {}))} nodes")
            else:
                print(f"  {path}: dict with {len(data)} entries, keys={keys}")
        elif isinstance(data, list):
            print(f"  {path}: list with {len(data)} items")
    else:
        print(f"  {path}: NOT FOUND")