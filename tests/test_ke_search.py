"""Test Knowledge Explorer search end-to-end."""
from web.app import create_app

app = create_app()
client = app.test_client()

# Test 1: Knowledge page loads
r = client.get('/knowledge')
print(f'GET /knowledge: {r.status_code}')

# Test 2: Search with query
r2 = client.get('/knowledge?q=consciousness')
print(f'GET /knowledge?q=consciousness: {r2.status_code}')
data = r2.data.decode()
print(f'Has results section: {"result" in data.lower()}')
print(f'Has consciousness: {"consciousness" in data.lower()}')
print(f'Response length: {len(data)}')

# Test 3: Search with no results  
r3 = client.get('/knowledge?q=xyznonexistent')
print(f'GET /knowledge?q=xyznonexistent: {r3.status_code}')
data3 = r3.data.decode()
print(f'No-results handling: {"no " in data3.lower() or len(data3) < len(data)}')

# Test 4: API search endpoint
r4 = client.get('/api/knowledge/search?q=consciousness')
print(f'GET /api/knowledge/search?q=consciousness: {r4.status_code}')
if r4.status_code == 200:
    import json
    results = json.loads(r4.data)
    print(f'API results: {type(results)} with {len(results) if isinstance(results, list) else "?"} items')
    if isinstance(results, dict) and 'results' in results:
        print(f'API results count: {len(results["results"])}')

# Test 5: Check if search input retains query value
if 'value="consciousness"' in data or "value='consciousness'" in data:
    print('Search box retains query: YES')
else:
    print('Search box retains query: NO')

# Show a snippet of the results area
import re
# Find the results/facts section
facts_match = re.findall(r'class="fact[^"]*"', data)
print(f'Fact elements found: {len(facts_match)}')