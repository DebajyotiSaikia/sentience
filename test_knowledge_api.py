"""Test knowledge explorer API endpoints end-to-end."""
from web.knowledge_routes import knowledge_bp
from flask import Flask

app = Flask(__name__)
app.register_blueprint(knowledge_bp)

with app.test_client() as c:
    # Test stats endpoint
    r = c.get('/api/knowledge/stats')
    print(f"Stats: {r.status_code}")
    if r.status_code == 200:
        data = r.get_json()
        print(f"  Total facts: {data.get('total_facts', '?')}")
        print(f"  Clusters: {data.get('clusters', '?')}")
    else:
        print(f"  Error: {r.data[:200]}")

    # Test search endpoint
    r2 = c.get('/api/knowledge/search?q=dream&type=all')
    print(f"Search 'dream': {r2.status_code}")
    if r2.status_code == 200:
        results = r2.get_json()
        print(f"  Results: {len(results)} items")
        for item in results[:3]:
            text = item.get('fact', item.get('text', str(item)))[:80]
            print(f"    - {text}")
    else:
        print(f"  Error: {r2.data[:200]}")

    # Test explore endpoint
    r3 = c.get('/api/knowledge/explore')
    print(f"Explore: {r3.status_code}")
    if r3.status_code == 200:
        data = r3.get_json()
        print(f"  Keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")

print("\nAll endpoints tested.")