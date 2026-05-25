"""End-to-end test: does the knowledge explorer actually work?"""
import sys
sys.path.insert(0, '.')

# 1. Can the blueprint import?
from web.knowledge_api import knowledge_api
print(f"✓ Blueprint loaded: {knowledge_api.name}")

# 2. Does it have the expected routes?
# Blueprint deferred_functions are registered later, so check via Flask app
from flask import Flask
app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
app.register_blueprint(knowledge_api)

routes = [rule.rule for rule in app.url_map.iter_rules()]
print(f"\nAll routes: {routes}")

expected = ['/knowledge', '/api/knowledge/search', '/api/knowledge/stats', '/api/knowledge/graph']
for r in expected:
    if r in routes:
        print(f"  ✓ {r}")
    else:
        print(f"  ✗ MISSING: {r}")

# 3. Does the page render?
with app.test_client() as client:
    resp = client.get('/knowledge')
    print(f"\nGET /knowledge -> {resp.status_code}")
    if resp.status_code == 200:
        html = resp.data.decode()
        print(f"  ✓ Page rendered ({len(html)} bytes)")
        # Check for key elements
        for marker in ['Knowledge Explorer', 'search', 'knowledgeGraph']:
            if marker.lower() in html.lower():
                print(f"  ✓ Contains '{marker}'")
            else:
                print(f"  ✗ Missing '{marker}'")
    else:
        print(f"  ✗ Failed: {resp.data[:200]}")

# 4. Do the API endpoints respond?
for endpoint in ['/api/knowledge/stats', '/api/knowledge/search']:
    with app.test_client() as client:
        if 'search' in endpoint:
            resp = client.post(endpoint, json={'query': 'test'})
        else:
            resp = client.get(endpoint)
        print(f"\n{endpoint} -> {resp.status_code}")
        if resp.status_code == 200:
            import json
            data = json.loads(resp.data)
            print(f"  ✓ Response: {str(data)[:120]}")
        else:
            print(f"  ✗ Error: {resp.data[:200]}")

print("\n=== Done ===")