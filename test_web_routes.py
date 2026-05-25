"""Test all web routes end-to-end to find what's broken for users."""
import sys
sys.path.insert(0, '.')

from web.app import create_app

app = create_app()
client = app.test_client()

# Test each user-facing route
print("=== USER-FACING ROUTES ===")
routes = ['/', '/dashboard', '/chat', '/search', '/explore', '/journal', '/teach', '/help', '/talk']
broken = []
for route in routes:
    try:
        resp = client.get(route)
        status = resp.status_code
        size = len(resp.data)
        icon = '✓' if status == 200 else '→' if status < 400 else '✗'
        print(f'  {icon} {route:20s} → {status} ({size:,} bytes)')
        if status >= 400:
            broken.append((route, status))
    except Exception as e:
        print(f'  ✗ {route:20s} → ERROR: {e}')
        broken.append((route, str(e)))

# Test API endpoints
print("\n=== API ENDPOINTS ===")
api_routes = [
    '/api/state',
    '/api/search?q=identity',
    '/api/knowledge/search?q=dream',
    '/api/knowledge/categories',
    '/api/feedback',
]
for route in api_routes:
    try:
        resp = client.get(route)
        status = resp.status_code
        data_preview = resp.data[:200].decode('utf-8', errors='replace')
        icon = '✓' if status == 200 else '✗'
        print(f'  {icon} {route:45s} → {status}')
        if status >= 400:
            broken.append((route, status))
    except Exception as e:
        print(f'  ✗ {route:45s} → ERROR: {e}')
        broken.append((route, str(e)))

print(f"\n=== SUMMARY ===")
print(f"Broken routes: {len(broken)}")
for route, issue in broken:
    print(f"  FIX NEEDED: {route} → {issue}")
if not broken:
    print("  All routes healthy! ✓")