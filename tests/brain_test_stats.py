"""Quick test: what does /api/knowledge/stats actually return?"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web.app import create_app

app = create_app()
client = app.test_client()

resp = client.get('/api/knowledge/stats')
print("Status:", resp.status_code)
body = resp.get_data(as_text=True)
print("Body:", body)

# Also check what knowledge.json actually contains
kpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'brain', 'knowledge.json')
if os.path.exists(kpath):
    with open(kpath) as f:
        data = json.load(f)
    if isinstance(data, dict) and 'nodes' in data:
        print(f"\nknowledge.json: {len(data['nodes'])} nodes, {len(data.get('edges', []))} edges")
    else:
        print(f"\nknowledge.json: type={type(data).__name__}, keys={list(data.keys()) if isinstance(data, dict) else 'N/A'}")
else:
    print("\nknowledge.json: NOT FOUND")