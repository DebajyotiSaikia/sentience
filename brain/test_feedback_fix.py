"""Diagnose why feedback POST returns 404."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# Check all registered routes
print("=== All registered routes ===")
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    if 'feedback' in rule.rule or 'api' in rule.rule:
        print(f"  {rule.methods} {rule.rule} -> {rule.endpoint}")

# Test feedback POST
print("\n=== Testing feedback POST ===")
import json
resp = client.post('/api/feedback', 
    data=json.dumps({"rating": 4, "message": "test", "context": "test"}),
    content_type='application/json')
print(f"POST /api/feedback: {resp.status_code}")
if resp.status_code != 200:
    print(f"  Body: {resp.data[:300]}")

# Also try without JSON content type
resp2 = client.post('/api/feedback',
    data={"rating": "4", "message": "test", "context": "test"})
print(f"POST /api/feedback (form): {resp2.status_code}")
if resp2.status_code != 200:
    print(f"  Body: {resp2.data[:300]}")

# Check knowledge stats endpoint  
print("\n=== Knowledge Stats ===")
resp3 = client.get('/api/knowledge/stats')
print(f"GET /api/knowledge/stats: {resp3.status_code}")
if resp3.status_code == 200:
    print(f"  {resp3.get_json()}")
else:
    print(f"  Body: {resp3.data[:300]}")

# Also check the main search
print("\n=== Search Test ===")
for q in ['emotion', 'identity', 'dream']:
    resp = client.get(f'/api/search?q={q}')
    data = resp.get_json() if resp.status_code == 200 else {}
    results = data.get('results', [])
    print(f'  "{q}": {resp.status_code}, {len(results)} results')