import json

d = json.load(open('brain/knowledge.json'))
nodes = d.get('nodes', {})
edges = d.get('edges', [])

print(f"Nodes: {len(nodes)}, Edges: {len(edges)}")
print(f"Node container type: {type(nodes).__name__}")

if isinstance(nodes, dict):
    for i, (k, v) in enumerate(nodes.items()):
        if i >= 3: break
        print(f"\n--- Node '{k}' ---")
        print(json.dumps(v, indent=2)[:400])
elif isinstance(nodes, list):
    for i, n in enumerate(nodes[:3]):
        print(f"\n--- Node {i} ---")
        print(json.dumps(n, indent=2)[:400])

if edges:
    print(f"\n--- First 3 edges ---")
    for e in edges[:3]:
        print(json.dumps(e)[:200])

# Now check what synthesis expects
print("\n=== Checking synthesis module ===")
import importlib.util
spec = importlib.util.find_spec("engine.knowledge_synthesis")
if spec:
    print(f"Synthesis module found at: {spec.origin}")
    with open(spec.origin) as f:
        content = f.read()
    # Find where it reads data from
    for line in content.split('\n'):
        if 'json' in line.lower() or 'knowledge' in line.lower() or 'path' in line.lower() or 'load' in line.lower():
            print(f"  >> {line.strip()}")
else:
    print("No synthesis module found!")