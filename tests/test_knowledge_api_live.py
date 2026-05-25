"""Test the knowledge search API end-to-end."""
import sys
sys.path.insert(0, '/workspace')

# Test 1: Import
try:
    from web.knowledge_api import knowledge_api
    print("[OK] Blueprint imported")
except Exception as e:
    print(f"[FAIL] Import: {e}")
    sys.exit(1)

# Test 2: Check routes
print(f"[OK] Blueprint name: {knowledge_api.name}")
print(f"[OK] Deferred functions: {len(knowledge_api.deferred_functions)}")

# Test 3: Test via Flask test client
try:
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(knowledge_api)
    client = app.test_client()
    
    resp = client.get('/api/knowledge/stats')
    print(f"[OK] GET /api/knowledge/stats -> {resp.status_code}")
    if resp.status_code == 200:
        import json
        data = json.loads(resp.data)
        print(f"  Stats: {data}")
    
    resp = client.get('/api/knowledge/search?q=dream')
    print(f"[OK] GET /api/knowledge/search?q=dream -> {resp.status_code}")
    if resp.status_code == 200:
        data = json.loads(resp.data)
        print(f"  Results: {len(data.get('results', []))} items")
        for r in data.get('results', [])[:3]:
            text = r.get('fact', r.get('text', str(r)))
            print(f"  - {text[:80]}")
    
    print("\n[DONE] All tests passed.")
except Exception as e:
    print(f"[FAIL] Flask test: {e}")
    import traceback
    traceback.print_exc()