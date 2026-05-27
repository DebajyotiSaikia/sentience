"""Quick diagnostic: what does /api/knowledge/stats actually return?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# Check the stats endpoint
resp = client.get('/api/knowledge/stats')
print(f"Status: {resp.status_code}")
print(f"Data: {resp.get_data(as_text=True)[:500]}")

# Check what knowledge files actually exist and have content
import json
paths = [
    'brain/knowledge.json',
    'persist/knowledge_graph.json',
]
for p in paths:
    full = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), p)
    if os.path.exists(full):
        with open(full) as f:
            data = json.load(f)
        if isinstance(data, dict):
            nodes = data.get('nodes', data)
            print(f"\n{p}: {len(nodes)} entries (dict)")
        elif isinstance(data, list):
            print(f"\n{p}: {len(data)} entries (list)")
    else:
        print(f"\n{p}: FILE NOT FOUND")

# Also check what the search endpoint returns
resp2 = client.get('/api/knowledge/search?q=identity')
print(f"\nSearch 'identity': {resp2.status_code}")
print(f"Data: {resp2.get_data(as_text=True)[:300]}")