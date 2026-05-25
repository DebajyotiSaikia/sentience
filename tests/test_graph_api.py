from web.app import create_app
app = create_app()
client = app.test_client()

r = client.get('/api/graph')
print(f'Status: {r.status_code}')

import json
try:
    data = json.loads(r.data)
    print(f'Nodes: {len(data.get("nodes", []))}')
    print(f'Edges: {len(data.get("edges", []))}')
    if data.get("nodes"):
        n = data["nodes"][0]
        print(f'Sample node keys: {list(n.keys())}')
        types = set(node.get("type","?") for node in data["nodes"])
        print(f'Node types: {types}')
    print("API is working.")
except Exception as e:
    print(f'Error: {e}')
    print(r.data[:300].decode("utf-8", errors="replace"))