import os
import json

# Check where knowledge.json actually lives
paths = [
    'persist/knowledge.json',
    'persist/knowledge_graph.json',
    'web/../persist/knowledge.json',
]

for p in paths:
    resolved = os.path.abspath(p)
    exists = os.path.exists(resolved)
    if exists:
        with open(resolved) as f:
            data = json.load(f)
        if isinstance(data, dict):
            print(f"{p} -> EXISTS (dict with {len(data)} keys)")
            sample_keys = list(data.keys())[:3]
            for k in sample_keys:
                v = data[k]
                if isinstance(v, dict):
                    print(f"  [{k}]: {list(v.keys())}")
                else:
                    print(f"  [{k}]: {type(v).__name__} = {str(v)[:80]}")
        elif isinstance(data, list):
            print(f"{p} -> EXISTS (list with {len(data)} items)")
            if data:
                print(f"  [0]: {str(data[0])[:100]}")
        else:
            print(f"{p} -> EXISTS ({type(data).__name__})")
    else:
        print(f"{p} -> MISSING")

# Now check what the web app actually loads
print("\n--- Checking web app knowledge loading ---")
from web.app import create_app
app = create_app()

with app.test_client() as client:
    # Test the stats endpoint
    resp = client.get('/api/knowledge/stats')
    if resp.status_code == 200:
        stats = resp.get_json()
        print(f"Stats API: {json.dumps(stats, indent=2)}")
    else:
        print(f"Stats API: {resp.status_code}")

    # Test the search endpoint  
    resp = client.get('/api/knowledge/search?q=agent')
    if resp.status_code == 200:
        results = resp.get_json()
        print(f"Search API for 'agent': {len(results.get('results', []))} results")
    else:
        print(f"Search API: {resp.status_code}")