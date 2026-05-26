"""Get the actual error when hitting root /"""
import traceback
import sys
sys.path.insert(0, '/workspace')

from web.app import create_app

app = create_app()
app.config['TESTING'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True

client = app.test_client()

# Test root
try:
    r = client.get('/')
    print(f"/ -> {r.status_code}")
    if r.status_code >= 400:
        print(r.data[:2000].decode(errors='replace'))
except Exception as e:
    print(f"/ -> ERROR: {e}")
    traceback.print_exc()

# Test /search
try:
    r = client.get('/search')
    print(f"\n/search -> {r.status_code}")
    if r.status_code >= 400:
        print(r.data[:2000].decode(errors='replace'))
except Exception as e:
    print(f"/search -> ERROR: {e}")
    traceback.print_exc()

# List all routes
print("\n--- All Routes ---")
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    print(f"  {rule.rule} -> {rule.endpoint} [{', '.join(rule.methods - {'HEAD', 'OPTIONS'})}]")