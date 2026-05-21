import json

data = json.load(open('brain/knowledge.json'))
print(f"Top-level keys: {list(data.keys())}")

nodes = data.get('nodes', data.get('facts', {}))
print(f"Type of nodes: {type(nodes).__name__}, count: {len(nodes)}")

# Handle both dict and list
if isinstance(nodes, dict):
    items = list(nodes.items())[:5]
    for key, val in items:
        print(f"\n--- Node key: {key} ---")
        if isinstance(val, dict):
            for k, v in val.items():
                print(f"  {k}: {str(v)[:120]}")
        else:
            print(f"  value: {str(val)[:200]}")
elif isinstance(nodes, list):
    for node in nodes[:5]:
        print(f"\n--- Node ---")
        if isinstance(node, dict):
            for k, v in node.items():
                print(f"  {k}: {str(v)[:120]}")
        else:
            print(f"  {str(node)[:200]}")