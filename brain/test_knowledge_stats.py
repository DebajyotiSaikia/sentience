"""Diagnose why /api/knowledge/stats reports 0 facts."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path

# Check what knowledge_api.py would find
BRAIN_DIR = Path(__file__).parent.parent / 'brain'
knowledge_path = BRAIN_DIR / 'knowledge.json'

print(f"Knowledge path: {knowledge_path}")
print(f"Exists: {knowledge_path.exists()}")

if knowledge_path.exists():
    with open(knowledge_path) as f:
        data = json.load(f)
    print(f"Type: {type(data)}")
    if isinstance(data, dict):
        print(f"Keys: {list(data.keys())}")
        nodes = data.get('nodes', {})
        print(f"Nodes type: {type(nodes)}, count: {len(nodes)}")
        if nodes:
            first_key = list(nodes.keys())[0]
            print(f"First node key: {first_key}")
            print(f"First node value: {nodes[first_key]}")
    else:
        print(f"Not a dict? Length: {len(data)}")

# Now test via the actual Flask endpoint
from web.app import create_app
app = create_app()
client = app.test_client()

resp = client.get('/api/knowledge/stats')
print(f"\n/api/knowledge/stats status: {resp.status_code}")
print(f"Response: {resp.get_data(as_text=True)[:500]}")