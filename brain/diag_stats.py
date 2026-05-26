"""Diagnose why /api/knowledge/stats returns 0 facts."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app

app = create_app()
client = app.test_client()

# Test the stats endpoint
resp = client.get('/api/knowledge/stats')
print(f"Status: {resp.status_code}")
print(f"Body: {resp.get_data(as_text=True)[:500]}")

# Also check the raw knowledge file
import json
kpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'brain', 'knowledge.json')
print(f"\nKnowledge file exists: {os.path.exists(kpath)}")
if os.path.exists(kpath):
    with open(kpath) as f:
        data = json.load(f)
    if isinstance(data, dict):
        print(f"Keys: {list(data.keys())}")
        if 'nodes' in data:
            print(f"Node count: {len(data['nodes'])}")
        else:
            print(f"Top-level dict with {len(data)} entries")
    elif isinstance(data, list):
        print(f"List with {len(data)} entries")