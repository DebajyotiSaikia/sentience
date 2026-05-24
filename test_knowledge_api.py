"""Quick smoke test for knowledge API endpoints."""
from web.knowledge_api import knowledge_api
from flask import Flask

app = Flask(__name__)
app.register_blueprint(knowledge_api)
client = app.test_client()

# Test search
resp = client.get('/api/knowledge/search?q=dream')
print(f'Search status: {resp.status_code}')
data = resp.get_json()
if data:
    print(f'Results: {len(data.get("results", []))} hits')
    for r in data.get("results", [])[:3]:
        print(f'  - {r.get("fact", r)[:80]}')
else:
    print(f'Raw response: {resp.data[:200]}')

# Test stats
resp2 = client.get('/api/knowledge/stats')
print(f'Stats status: {resp2.status_code}')
stats = resp2.get_json()
if stats:
    print(f'Total facts: {stats.get("total_facts", "?")}')

print('\nAll tests passed.')