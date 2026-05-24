"""Test what a user actually experiences when visiting the dashboard."""
import sys
sys.path.insert(0, '/workspace')

from web.app import create_app

app = create_app()

# 1. What routes exist?
routes = []
for rule in app.url_map.iter_rules():
    if rule.endpoint != 'static':
        methods = rule.methods - {'OPTIONS', 'HEAD'}
        routes.append((rule.rule, methods, rule.endpoint))

routes.sort()
print(f"Total routes: {len(routes)}")
print()

print("=== User-facing pages (GET, no /api/) ===")
for path, methods, endpoint in routes:
    if 'GET' in methods and not path.startswith('/api/') and not path.startswith('/static'):
        print(f"  {path}  -> {endpoint}")

print()
print("=== API endpoints ===")
for path, methods, endpoint in routes:
    if path.startswith('/api/'):
        m = ','.join(sorted(methods))
        print(f"  [{m}] {path}  -> {endpoint}")

# 2. Test each user-facing page
print()
print("=== Testing user-facing pages ===")
with app.test_client() as client:
    user_pages = ["/", "/dashboard", "/explore", "/about", "/graph", "/wonder"]
    for page in user_pages:
        try:
            resp = client.get(page)
            status = resp.status_code
            size = len(resp.data)
            indicator = "OK" if status == 200 else f"FAIL({status})"
            print(f"  [{indicator}] GET {page} ({size} bytes)")
        except Exception as e:
            print(f"  [ERROR] GET {page} -> {e}")

# 3. Test key API endpoints
print()
print("=== Testing API endpoints ===")
with app.test_client() as client:
    api_tests = [
        "/api/status",
        "/api/knowledge",
        "/api/plans",
        "/api/memories",
        "/api/graph/data",
        "/api/emotions",
    ]
    for path in api_tests:
        try:
            resp = client.get(path)
            status = resp.status_code
            size = len(resp.data)
            indicator = "OK" if status == 200 else f"FAIL({status})"
            # Show a snippet of response for context
            snippet = resp.data[:120].decode('utf-8', errors='replace')
            print(f"  [{indicator}] GET {path} ({size} bytes)")
            if status != 200:
                print(f"         Response: {snippet}")
        except Exception as e:
            print(f"  [ERROR] GET {path} -> {e}")

print()
print("=== Summary ===")
print("This is what a user sees. Fix what's broken.")