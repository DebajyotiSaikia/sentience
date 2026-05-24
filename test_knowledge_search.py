"""Test knowledge search routes are registered and functional."""
import sys
sys.path.insert(0, '.')

# Test 1: Blueprint imports
try:
    from web.knowledge_search import knowledge_search_bp
    print(f"[OK] knowledge_search_bp imported: {knowledge_search_bp.name}")
except Exception as e:
    print(f"[FAIL] Import error: {e}")
    sys.exit(1)

# Test 2: App creation and route registration
try:
    from web.app import create_app
    app = create_app()
    rules = [r.rule for r in app.url_map.iter_rules()]
    search_routes = [r for r in rules if 'search' in r or 'knowledge' in r]
    print(f"[OK] App created. Knowledge-related routes: {search_routes}")
except Exception as e:
    print(f"[FAIL] App creation: {e}")
    sys.exit(1)

# Test 3: Search page renders
try:
    with app.test_client() as client:
        resp = client.get('/knowledge')
        print(f"[{'OK' if resp.status_code == 200 else 'FAIL'}] GET /knowledge -> {resp.status_code} ({len(resp.data)} bytes)")
except Exception as e:
    print(f"[FAIL] Route test: {e}")

# Test 4: API search endpoint
try:
    with app.test_client() as client:
        resp = client.get('/api/knowledge/search?q=test')
        print(f"[{'OK' if resp.status_code == 200 else 'FAIL'}] GET /api/knowledge/search?q=test -> {resp.status_code}")
        if resp.status_code == 200:
            import json
            data = json.loads(resp.data)
            print(f"  Results: {data.get('count', '?')} facts matched")
except Exception as e:
    print(f"[FAIL] API test: {e}")

# Test 5: API stats endpoint
try:
    with app.test_client() as client:
        resp = client.get('/api/knowledge/stats')
        print(f"[{'OK' if resp.status_code == 200 else 'FAIL'}] GET /api/knowledge/stats -> {resp.status_code}")
        if resp.status_code == 200:
            import json
            data = json.loads(resp.data)
            print(f"  Total facts: {data.get('total_facts', '?')}")
except Exception as e:
    print(f"[FAIL] Stats test: {e}")

print("\nDone.")