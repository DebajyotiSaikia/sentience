"""Check what API/chat routes are registered."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
app = create_app()

print("=== API and Chat Routes ===")
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    if '/api/' in rule.rule or 'chat' in rule.rule:
        methods = ','.join(sorted(rule.methods - {'OPTIONS', 'HEAD'}))
        print(f"  {methods:8s} {rule.rule:40s} -> {rule.endpoint}")

print("\n=== Testing POST /api/chat ===")
client = app.test_client()
import json
resp = client.post('/api/chat',
    data=json.dumps({'message': 'hello'}),
    content_type='application/json')
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    print(f"Response: {resp.get_data(as_text=True)[:300]}")
else:
    print(f"Body: {resp.get_data(as_text=True)[:200]}")