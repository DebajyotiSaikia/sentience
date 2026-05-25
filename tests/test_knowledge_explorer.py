"""Test that the knowledge explorer module loads and routes are registered."""
import sys
sys.path.insert(0, '.')

# Test 1: Module imports cleanly
try:
    from web.knowledge_explorer import knowledge_explorer_bp
    print(f"[PASS] Module imports. Blueprint name: {knowledge_explorer_bp.name}")
except Exception as e:
    print(f"[FAIL] Import error: {e}")
    sys.exit(1)

# Test 2: Check routes are registered
routes = []
for rule in knowledge_explorer_bp.deferred_functions:
    routes.append(str(rule))
print(f"[INFO] Deferred functions: {len(routes)}")

# Test 3: Flask app integration
try:
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(knowledge_explorer_bp)
    
    registered = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            registered.append(f"  {rule.rule} -> {rule.endpoint}")
    
    print(f"[PASS] Registered {len(registered)} routes:")
    for r in sorted(registered):
        print(r)
except Exception as e:
    print(f"[FAIL] Flask integration: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Hit the API endpoints with test client
try:
    client = app.test_client()
    
    endpoints = [
        '/api/knowledge/stats',
        '/api/knowledge/search?q=test',
        '/api/knowledge/clusters',
        '/api/knowledge/questions',
    ]
    
    for ep in endpoints:
        resp = client.get(ep)
        status = "PASS" if resp.status_code == 200 else "FAIL"
        print(f"[{status}] GET {ep} -> {resp.status_code}")
        if resp.status_code != 200:
            print(f"       Body: {resp.data[:200]}")
    
    # Test the main page
    resp = client.get('/knowledge')
    status = "PASS" if resp.status_code == 200 else "FAIL"
    print(f"[{status}] GET /knowledge -> {resp.status_code}")
    
except Exception as e:
    print(f"[FAIL] Test client: {e}")
    import traceback
    traceback.print_exc()

print("\n[DONE] Knowledge explorer test complete.")