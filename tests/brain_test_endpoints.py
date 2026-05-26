"""Quick test of the 4 failing UX audit endpoints."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# 1. Knowledge stats
r = client.get('/api/knowledge/stats')
print(f"[1] /api/knowledge/stats — {r.status_code}")
data = r.get_json(silent=True) or {}
print(f"    total_facts={data.get('total_facts', '???')}")
print(f"    Body preview: {r.get_data(as_text=True)[:200]}")
print()

# 2. Knowledge search
r = client.get('/api/knowledge/search?q=emotion')
print(f"[2] /api/knowledge/search?q=emotion — {r.status_code}")
data = r.get_json(silent=True) or {}
results = data.get('results', [])
print(f"    results count={len(results)}")
print(f"    Body preview: {r.get_data(as_text=True)[:200]}")
print()

# 3. Home page content
r = client.get('/')
home = r.get_data(as_text=True)
print(f"[3] / (home) — {r.status_code}, length={len(home)}")
# Check for substantive content markers
has_name = 'XTAgent' in home
has_nav = 'Chat' in home or 'chat' in home
print(f"    has XTAgent mention: {has_name}")
print(f"    has nav links: {has_nav}")
print()

# 4. Chat API
r = client.post('/api/chat',
    data=json.dumps({'message': 'hello'}),
    content_type='application/json')
print(f"[4] POST /api/chat — {r.status_code}")
data = r.get_json(silent=True) or {}
response_text = data.get('response', '')
print(f"    response length={len(response_text)}")
print(f"    response preview: {response_text[:200]}")