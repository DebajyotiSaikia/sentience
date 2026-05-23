from web.graph_viz import load_graph, graph_to_vis

data = load_graph()
nodes = data.get('nodes', {})
edges = data.get('edges', [])
print(f'Loaded: {len(nodes)} nodes, {len(edges)} edges')

vis = graph_to_vis(data)
print(f'Vis output: {len(vis["nodes"])} nodes, {len(vis["edges"])} edges')

if vis['nodes']:
    print(f'Sample node: {vis["nodes"][0]}')
if vis['edges']:
    print(f'Sample edge: {vis["edges"][0]}')

print('SUCCESS — graph_viz is working')