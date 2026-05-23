import json

# Load knowledge graph
with open('brain/knowledge.json') as f:
    kg = json.load(f)

nodes = kg.get('nodes', kg)
print(f"Total nodes: {len(nodes)}")
print(f"Top-level keys in kg: {list(kg.keys())}")
print()

# Show structure of first 5 nodes
for i, (k, v) in enumerate(nodes.items()):
    if i >= 5:
        break
    if isinstance(v, dict):
        print(f"Node '{k[:60]}': keys={list(v.keys())}")
        for vk, vv in v.items():
            print(f"  {vk}: {repr(vv)[:80]}")
    else:
        print(f"Node '{k[:60]}': type={type(v).__name__}, val={repr(v)[:80]}")
    print()

# Check for nodes missing expected keys
missing_fact = []
missing_type = []
for k, v in nodes.items():
    if isinstance(v, dict):
        if 'fact' not in v:
            missing_fact.append(k[:50])
        if 'type' not in v:
            missing_type.append(k[:50])

print(f"Nodes missing 'fact' key: {len(missing_fact)}/{len(nodes)}")
if missing_fact[:5]:
    print(f"  Examples: {missing_fact[:5]}")
print(f"Nodes missing 'type' key: {len(missing_type)}/{len(nodes)}")