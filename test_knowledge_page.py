"""Test the redesigned knowledge explorer page."""
from web.app import create_app
import json

app = create_app()
client = app.test_client()

# Test knowledge page loads
resp = client.get('/knowledge')
print(f'/knowledge: {resp.status_code}')
if resp.status_code == 200:
    data = resp.data.decode()
    has_nav = 'xt-nav' in data
    has_search = 'ke-search' in data
    has_base = 'base.html' in data or '--bg' in data  # CSS vars from base
    print(f'  Has nav bar: {has_nav}')
    print(f'  Has search UI: {has_search}')
    print(f'  Uses base design: {has_base}')
    print(f'  Page length: {len(data)} chars')
    if not has_nav:
        print('  WARNING: Nav not rendering — template may not extend base.html')
else:
    print(f'  ERROR body: {resp.data.decode()[:500]}')

# Test knowledge search API
resp2 = client.get('/knowledge/search?q=consciousness')
print(f'\n/knowledge/search?q=consciousness: {resp2.status_code}')
if resp2.status_code == 200:
    results = json.loads(resp2.data)
    print(f'  Results: {len(results.get("results", []))} facts found')
    for r in results.get("results", [])[:3]:
        text = r.get("fact", r.get("text", str(r)))[:80]
        print(f'    - {text}')

# Check nav includes Knowledge/Explore link
resp3 = client.get('/help')
if resp3.status_code == 200:
    help_data = resp3.data.decode()
    has_explore = 'Explore' in help_data
    has_knowledge = 'Knowledge' in help_data
    print(f'\nNav links on /help page:')
    print(f'  Has "Explore": {has_explore}')
    print(f'  Has "Knowledge": {has_knowledge}')

# List all routes
print('\nAll registered routes:')
with app.app_context():
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        if not rule.rule.startswith('/static'):
            methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
            print(f'  {rule.rule} [{methods}]')