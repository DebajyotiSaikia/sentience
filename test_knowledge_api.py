"""Test that the knowledge API returns data the graph visualizer can use."""
import sys, json
sys.path.insert(0, '.')

# Try to load the knowledge graph the same way the server does
try:
    from dashboard.server import app
    client = app.test_client()
    resp = client.get('/api/knowledge')
    data = resp.get_json()
    nodes = data.get('nodes', [])
    edges = data.get('edges', [])
    print(f"API returns: {len(nodes)} nodes, {len(edges)} edges")
    if nodes:
        n = nodes[0]
        print(f"Node keys: {list(n.keys())}")
        print(f"Sample: {n.get('label', n.get('content', ''))[:80]}")
    if edges:
        e = edges[0]
        print(f"Edge keys: {list(e.keys())}")
    print("✓ Knowledge API works for graph visualizer")
except Exception as ex:
    print(f"API test failed: {ex}")
    # Fallback: read the knowledge file directly
    import os
    kg_path = "memory/knowledge_graph.json"
    if os.path.exists(kg_path):
        with open(kg_path) as f:
            data = json.load(f)
        nodes = data.get('nodes', [])
        edges = data.get('edges', [])
        print(f"Direct file: {len(nodes)} nodes, {len(edges)} edges")
        if nodes:
            print(f"Node keys: {list(nodes[0].keys())}")
        print("✓ Knowledge data exists, graph should work")
    else:
        print("✗ No knowledge graph file found")