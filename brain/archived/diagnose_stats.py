"""Diagnose: which blueprint serves /api/knowledge/stats and why does it return 0?"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()

# 1. Check which endpoint serves /api/knowledge/stats
with app.test_request_context():
    from flask import url_for
    for rule in app.url_map.iter_rules():
        if 'knowledge' in str(rule) and 'stats' in str(rule):
            print(f"Route: {rule} -> endpoint: {rule.endpoint}")

# 2. Hit it and see what we get
client = app.test_client()
resp = client.get('/api/knowledge/stats')
print(f"\nStatus: {resp.status_code}")
data = resp.get_json()
print(f"Response: {json.dumps(data, indent=2)[:500]}")

# 3. Check both data sources
for path in ['brain/knowledge.json', 'persist/knowledge_graph.json']:
    if os.path.exists(path):
        with open(path) as f:
            d = json.load(f)
        if isinstance(d, dict):
            nodes = d.get('nodes', d)
            print(f"\n{path}: {len(nodes)} entries (dict)")
        elif isinstance(d, list):
            print(f"\n{path}: {len(d)} entries (list)")
    else:
        print(f"\n{path}: DOES NOT EXIST")