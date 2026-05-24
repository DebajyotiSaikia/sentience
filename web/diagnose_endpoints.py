"""Direct diagnostic of knowledge endpoints — no server needed."""
import sys, os, traceback

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test 1: Can we import the blueprint?
print("=" * 60)
print("TEST 1: Import knowledge_unified blueprint")
print("=" * 60)
try:
    from web.knowledge_unified import knowledge_unified_bp as knowledge_bp
    print(f"  ✅ Imported: {knowledge_bp.name}")
except Exception as e:
    print(f"  ❌ Import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 2: Create a test Flask app and mount the blueprint
print("\n" + "=" * 60)
print("TEST 2: Mount blueprint and list routes")
print("=" * 60)
try:
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(knowledge_bp)
    with app.app_context():
        routes = []
        for rule in app.url_map.iter_rules():
            if 'knowledge' in rule.rule or 'static' not in rule.rule:
                routes.append(f"  {rule.rule} [{','.join(rule.methods - {'HEAD', 'OPTIONS'})}]")
        routes.sort()
        for r in routes:
            print(r)
        print(f"  Total: {len(routes)} routes")
except Exception as e:
    print(f"  ❌ Failed: {e}")
    traceback.print_exc()

# Test 3: Hit /api/knowledge/all directly
print("\n" + "=" * 60)
print("TEST 3: GET /api/knowledge/all")
print("=" * 60)
try:
    with app.test_client() as client:
        resp = client.get('/api/knowledge/all')
        print(f"  Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.get_json()
            print(f"  ✅ Items: {len(data) if isinstance(data, list) else 'not a list'}")
            if isinstance(data, list) and len(data) > 0:
                print(f"  Sample: {data[0]}")
        else:
            print(f"  ❌ Body: {resp.get_data(as_text=True)[:500]}")
except Exception as e:
    print(f"  ❌ Error: {e}")
    traceback.print_exc()

# Test 4: Hit /api/knowledge/graph
print("\n" + "=" * 60)
print("TEST 4: GET /api/knowledge/graph")
print("=" * 60)
try:
    with app.test_client() as client:
        resp = client.get('/api/knowledge/graph')
        print(f"  Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.get_json()
            if isinstance(data, dict):
                print(f"  ✅ Nodes: {len(data.get('nodes', []))}, Edges: {len(data.get('edges', []))}")
            else:
                print(f"  Data type: {type(data)}")
        else:
            print(f"  ❌ Body: {resp.get_data(as_text=True)[:500]}")
except Exception as e:
    print(f"  ❌ Error: {e}")
    traceback.print_exc()

# Test 5: Search for "dream"
print("\n" + "=" * 60)
print("TEST 5: GET /api/knowledge/search?q=dream")
print("=" * 60)
try:
    with app.test_client() as client:
        resp = client.get('/api/knowledge/search?q=dream')
        print(f"  Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.get_json()
            results = data.get('results', data) if isinstance(data, dict) else data
            print(f"  ✅ Results: {len(results) if isinstance(results, list) else results}")
            if isinstance(results, list) and len(results) > 0:
                print(f"  Sample: {str(results[0])[:200]}")
        else:
            print(f"  ❌ Body: {resp.get_data(as_text=True)[:500]}")
except Exception as e:
    print(f"  ❌ Error: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)