from web.app import create_app

app = create_app()
client = app.test_client()

# Test the graph API endpoint
resp = client.get('/graph/api/data')
print('API STATUS:', resp.status_code)
data = resp.get_data(as_text=True)
print('API DATA:', data[:500])
print()

# Test the graph page
resp2 = client.get('/graph/')
print('PAGE STATUS:', resp2.status_code)
print('PAGE SIZE:', len(resp2.get_data()), 'bytes')

# If API works, show node/edge counts
if resp.status_code == 200:
    import json
    d = json.loads(data)
    print(f"Nodes: {len(d.get('nodes', []))}")
    print(f"Edges: {len(d.get('edges', []))}")