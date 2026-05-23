import json

with open('brain/knowledge.json') as f:
    kg = json.load(f)

nodes = kg.get('nodes', kg)

# Show the structure of nodes that DON'T have 'fact'
print("=== Nodes missing 'fact' key ===")
for k, v in nodes.items():
    if isinstance(v, dict) and 'fact' not in v:
        print(f"\nNode '{k}':")
        for vk, vv in v.items():
            val_str = repr(vv)
            if len(val_str) > 120:
                val_str = val_str[:120] + "..."
            print(f"  {vk}: {val_str}")

# Also check edges
edges = kg.get('edges', [])
print(f"\n=== Edges: {len(edges)} total ===")
for e in edges[:5]:
    print(f"  {e}")