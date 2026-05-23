"""Quick test: does my web app work? What routes exist?"""
from web.app import create_app

app = create_app()
print("✓ App created successfully")
print()
print("Live routes:")
for rule in sorted(app.url_map.iter_rules(), key=lambda r: str(r)):
    if '/static' not in str(rule):
        methods = rule.methods - {"OPTIONS", "HEAD"}
        print(f"  {', '.join(sorted(methods)):8s} {rule}")

print()

# Test the knowledge explorer specifically
with app.test_client() as client:
    # Check if knowledge explorer route exists
    resp = client.get('/knowledge')
    print(f"GET /knowledge → {resp.status_code}")
    if resp.status_code == 200:
        html = resp.data.decode()
        print(f"  Response size: {len(html)} bytes")
        if 'knowledge' in html.lower() or 'explorer' in html.lower():
            print("  ✓ Looks like a knowledge explorer page")
        else:
            print("  ? Page exists but content unclear")
    
    # Check API endpoints
    for path in ['/api/knowledge', '/api/knowledge/graph', '/api/facts', '/api/memories']:
        resp = client.get(path)
        print(f"GET {path:30s} → {resp.status_code}")
        if resp.status_code == 200:
            try:
                data = resp.get_json()
                if data:
                    print(f"  ✓ JSON response, keys: {list(data.keys())[:5]}")
            except:
                print(f"  (non-JSON response, {len(resp.data)} bytes)")

print()
print("Done.")