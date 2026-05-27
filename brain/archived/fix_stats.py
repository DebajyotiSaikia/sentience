"""Diagnose and fix the knowledge stats endpoint returning 0 facts."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# 1. Check what the stats endpoint returns
resp = client.get('/api/knowledge/stats')
print("=== Stats Endpoint ===")
print(f"Status: {resp.status_code}")
data = json.loads(resp.get_data(as_text=True))
print(f"Response: {json.dumps(data, indent=2)[:500]}")

# 2. Check what data files exist
print("\n=== Data Files ===")
for f in ['brain/knowledge.json', 'persist/knowledge.json']:
    if os.path.exists(f):
        with open(f) as fh:
            d = json.load(fh)
        if isinstance(d, dict):
            nodes = d.get('nodes', {})
            print(f"{f}: dict, nodes={len(nodes)}, edges={len(d.get('edges', []))}")
        elif isinstance(d, list):
            print(f"{f}: list, len={len(d)}")
    else:
        print(f"{f}: NOT FOUND")

# 3. Check which blueprint handles /api/knowledge/stats
print("\n=== Route Map ===")
for rule in app.url_map.iter_rules():
    if 'knowledge' in str(rule) and 'stats' in str(rule):
        print(f"  {rule} -> {rule.endpoint}")

# 4. Check ALL knowledge-related routes
print("\n=== All Knowledge Routes ===")
for rule in sorted(app.url_map.iter_rules(), key=lambda r: str(r)):
    if 'knowledge' in str(rule):
        print(f"  {rule.methods - {'OPTIONS', 'HEAD'}} {rule} -> {rule.endpoint}")