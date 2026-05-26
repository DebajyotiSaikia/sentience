"""Diagnose and fix the knowledge stats endpoint returning 0 facts."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Step 1: What data actually exists?
kg_path = 'brain/knowledge.json'
if os.path.exists(kg_path):
    with open(kg_path) as f:
        data = json.load(f)
    if isinstance(data, dict) and 'nodes' in data:
        print(f"brain/knowledge.json: {len(data['nodes'])} nodes, {len(data.get('edges',[]))} edges")
    else:
        print(f"brain/knowledge.json: type={type(data).__name__}, len={len(data)}")
else:
    print("brain/knowledge.json: NOT FOUND")

pg_path = 'persist/knowledge_graph.json'
if os.path.exists(pg_path):
    with open(pg_path) as f:
        data2 = json.load(f)
    if isinstance(data2, dict):
        print(f"persist/knowledge_graph.json: {len(data2)} top-level keys")
        if 'nodes' in data2:
            print(f"  nodes: {len(data2['nodes'])}")
    else:
        print(f"persist/knowledge_graph.json: type={type(data2).__name__}, len={len(data2)}")
else:
    print("persist/knowledge_graph.json: NOT FOUND")

# Step 2: Test the stats endpoint
from web.app import create_app
app = create_app()
client = app.test_client()

for path in ['/api/knowledge/stats', '/api/knowledge', '/api/search']:
    resp = client.get(path)
    body = resp.get_data(as_text=True)[:300]
    print(f"\n{path}: {resp.status_code}")
    print(f"  {body}")