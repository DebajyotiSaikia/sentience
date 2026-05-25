"""Test: does the web app actually boot and serve key routes?"""
import sys
sys.path.insert(0, '/workspace')

print("=== Attempting to create Flask app ===")
try:
    from web.app import create_app
    app = create_app()
    print(f"  App created: {app.name}")
    print(f"  Total routes: {len(list(app.url_map.iter_rules()))}")
except Exception as e:
    print(f"  FAILED to create app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# List all routes
print("\n=== All registered routes ===")
routes = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
for rule in routes:
    methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
    print(f"  {methods:6s} {rule.rule}")

# Test key endpoints with test client
print("\n=== Testing key endpoints ===")
with app.test_client() as client:
    endpoints = [
        ('GET', '/'),
        ('GET', '/health'),
        ('GET', '/knowledge'),
        ('GET', '/api/knowledge/search?q=dream'),
        ('GET', '/api/knowledge/stats'),
        ('GET', '/graph'),
        ('GET', '/ask'),
        ('GET', '/explore'),
        ('GET', '/about'),
    ]
    for method, path in endpoints:
        try:
            resp = client.get(path) if method == 'GET' else client.post(path)
            status = resp.status_code
            size = len(resp.data)
            marker = '✓' if status < 400 else '✗'
            print(f"  {marker} {method} {path:40s} → {status} ({size} bytes)")
        except Exception as e:
            print(f"  ✗ {method} {path:40s} → ERROR: {e}")

print("\nDone.")