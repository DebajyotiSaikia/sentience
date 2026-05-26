"""Test that knowledge page loads and nav link exists."""
from web.app import create_app

app = create_app()
client = app.test_client()

# Test knowledge page loads
resp = client.get('/knowledge')
print(f'Knowledge page: {resp.status_code}')
if resp.status_code == 200:
    data = resp.data.decode()
    print(f'  Has nav: {"xt-nav" in data or "Knowledge" in data}')
    print(f'  Has search: {"search" in data.lower()}')
    print(f'  Length: {len(data)} chars')
else:
    print(f'  Body: {resp.data[:500]}')

# Test nav appears on other pages with knowledge link
resp2 = client.get('/help')
print(f'Help page: {resp2.status_code}')
if resp2.status_code == 200:
    has_knowledge_link = '/knowledge' in resp2.data.decode()
    print(f'  Has knowledge nav link: {has_knowledge_link}')

# Test knowledge search API
resp3 = client.get('/knowledge/search?q=consciousness')
print(f'Knowledge search API: {resp3.status_code}')
if resp3.status_code == 200:
    import json
    results = json.loads(resp3.data)
    print(f'  Results: {len(results.get("results", []))} facts found')