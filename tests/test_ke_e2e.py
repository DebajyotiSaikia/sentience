"""End-to-end test of knowledge explorer for user alignment assessment."""
import sys, json
sys.path.insert(0, '.')

from web.app import create_app
app = create_app()
client = app.test_client()

# Test 1: Knowledge explorer page loads
r = client.get('/knowledge')
print(f'GET /knowledge: {r.status_code} ({len(r.data)} bytes)')
if r.status_code == 200:
    html = r.data.decode()
    has_search = 'search' in html.lower()
    has_facts = 'fact' in html.lower()
    print(f'  Has search UI: {has_search}')
    print(f'  Has facts: {has_facts}')
else:
    print(f'  ERROR: {r.data.decode()[:200]}')

# Test 2: Search API
r2 = client.get('/api/knowledge/search?q=consciousness')
print(f'GET /api/knowledge/search?q=consciousness: {r2.status_code}')
if r2.status_code == 200:
    data = json.loads(r2.data)
    print(f'  Results: {data.get("total", "?")}')
    for res in data.get('results', [])[:3]:
        fact_text = res.get('fact', '') if isinstance(res, dict) else str(res)
        print(f'    - {fact_text[:80]}')
elif r2.status_code == 404:
    print('  MISSING - search endpoint not registered')

# Test 3: Stats API
r3 = client.get('/api/knowledge/stats')
print(f'GET /api/knowledge/stats: {r3.status_code}')
if r3.status_code == 200:
    data = json.loads(r3.data)
    print(f'  Total facts: {data.get("total_facts", "?")}')
    cats = data.get('categories', {})
    print(f'  Categories: {list(cats.keys())[:5]}')

# Test 4: Random fact
r4 = client.get('/api/knowledge/random')
print(f'GET /api/knowledge/random: {r4.status_code}')
if r4.status_code == 200:
    data = json.loads(r4.data)
    fact = data.get('fact', '')
    print(f'  Random fact: {str(fact)[:80]}')

# Test 5: Chat page
r5 = client.get('/chat')
print(f'GET /chat: {r5.status_code}')

# Test 6: Home page  
r6 = client.get('/')
print(f'GET /: {r6.status_code}')

# Test 7: List all registered routes
print('\n--- All registered routes ---')
with app.app_context():
    rules = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
    for rule in rules:
        if not rule.rule.startswith('/static'):
            methods = ','.join(sorted(rule.methods - {'OPTIONS', 'HEAD'}))
            print(f'  {methods:6s} {rule.rule}')