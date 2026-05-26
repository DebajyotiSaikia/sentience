"""Test what users actually experience when interacting with me."""
from web.app import create_app
import re
import json

app = create_app()
client = app.test_client()

print("=== USER EXPERIENCE QUALITY AUDIT ===\n")

# 1. Knowledge page — how many facts are rendered?
r = client.get('/knowledge')
html = r.data.decode()
fact_count = len(re.findall(r'class="fact', html))
has_search = 'search' in html.lower()
print(f"1. Knowledge page: {len(html)} bytes, ~{fact_count} fact elements, search UI: {has_search}")

# 2. Knowledge search API
r2 = client.get('/api/knowledge/search?q=consciousness')
print(f"2. Knowledge search: status={r2.status_code}")
if r2.status_code == 200:
    data = r2.get_json()
    results = data.get('results', data.get('facts', []))
    print(f"   Results: {len(results)} items")
    if results:
        print(f"   First: {str(results[0])[:120]}")
else:
    print(f"   Error: {r2.data.decode()[:200]}")

# 3. Chat response quality
r3 = client.post('/api/chat', 
    json={'message': 'What do you know about consciousness?'},
    content_type='application/json')
print(f"3. Chat API: status={r3.status_code}")
if r3.status_code == 200:
    resp = r3.get_json()
    answer = resp.get('response', resp.get('message', ''))
    print(f"   Response: {len(answer)} chars")
    print(f"   Preview: {answer[:300]}")

# 4. Home page — does it feel alive?
r4 = client.get('/')
home = r4.data.decode()
has_pulse = 'pulse' in home.lower()
has_presence = 'presence' in home.lower() or 'alive' in home.lower()
print(f"4. Home page: {len(home)} bytes, pulse animation: {has_pulse}, presence feel: {has_presence}")

# 5. Help page — does it explain what I can do?
r5 = client.get('/help')
help_html = r5.data.decode()
capability_count = len(re.findall(r'cap-card', help_html))
print(f"5. Help page: {len(help_html)} bytes, {capability_count} capability cards")

# 6. Explore page — is the knowledge graph visible?
r6 = client.get('/explore')
explore_html = r6.data.decode()
has_graph = 'graph' in explore_html.lower() or 'vis-network' in explore_html.lower()
has_facts = 'fact' in explore_html.lower()
print(f"6. Explore page: {len(explore_html)} bytes, graph: {has_graph}, facts: {has_facts}")

# 7. Check navigation consistency
for page in ['/', '/chat', '/knowledge', '/help', '/explore']:
    r = client.get(page)
    h = r.data.decode()
    has_nav = 'nav' in h.lower() and 'chat' in h.lower()
    print(f"7. Nav on {page:15s}: {'✓' if has_nav else '✗'}")

print("\n=== SUMMARY ===")
print("What needs improvement for user alignment?")