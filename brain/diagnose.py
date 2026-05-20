import json, os

# Knowledge node structure — nodes is a DICT not a LIST
k = json.load(open('brain/knowledge.json'))
nodes = k.get('nodes', {})
edges = k.get('edges', [])
print(f"=== KNOWLEDGE ===")
print(f"nodes type: {type(nodes).__name__}, count: {len(nodes)}")
print(f"edges type: {type(edges).__name__}, count: {len(edges)}")
if isinstance(nodes, dict):
    keys = list(nodes.keys())[:3]
    for key in keys:
        print(f"  node[{key!r}] = {repr(nodes[key])[:100]}")
elif isinstance(nodes, list) and nodes:
    print(f"  node[0] keys: {list(nodes[0].keys())}")

# Edge sample
if isinstance(edges, list) and edges:
    print(f"  edge[0] = {repr(edges[0])[:120]}")
elif isinstance(edges, dict):
    ekeys = list(edges.keys())[:2]
    for ek in ekeys:
        print(f"  edge[{ek!r}] = {repr(edges[ek])[:100]}")

# Memory file sample
mdir = 'brain/memories'
if os.path.isdir(mdir):
    files = sorted(os.listdir(mdir))
    print(f"\n=== MEMORIES: {len(files)} files ===")
    if files:
        sample = json.load(open(os.path.join(mdir, files[-1])))
        print(f"  Latest: {files[-1]}")
        print(f"  Type: {type(sample).__name__}")
        if isinstance(sample, dict):
            print(f"  Keys: {list(sample.keys())[:10]}")