"""Final end-to-end test for knowledge explorer."""
import sys
sys.path.insert(0, '.')

from web.app import create_app

app = create_app()
client = app.test_client()

# Test 1: Knowledge page loads with nav
r = client.get('/knowledge')
print(f'GET /knowledge: {r.status_code}')
html = r.data.decode()
has_nav = 'xt-nav' in html or 'navbar' in html.lower()[:2000]
has_title = 'Knowledge Explorer' in html
print(f'  Nav present: {has_nav}')
print(f'  Title present: {has_title}')

# Test 2: Search works
r2 = client.get('/knowledge?q=consciousness')
print(f'GET /knowledge?q=consciousness: {r2.status_code}')

# Test 3: API endpoint
r3 = client.get('/api/knowledge/search?q=emotion')
print(f'GET /api/knowledge/search?q=emotion: {r3.status_code}')
if r3.status_code == 200:
    data = r3.get_json()
    print(f'  Results: {len(data.get("results", []))} items')

# Test 4: Stats API
r4 = client.get('/api/knowledge/stats')
print(f'GET /api/knowledge/stats: {r4.status_code}')
if r4.status_code == 200:
    stats = r4.get_json()
    print(f'  Total facts: {stats.get("total_facts", "?")}')

print()
codes = [r.status_code, r2.status_code, r3.status_code, r4.status_code]
if all(c == 200 for c in codes):
    print('=== ALL TESTS PASSED ===')
else:
    print(f'=== FAILURES: {[c for c in codes if c != 200]} ===')