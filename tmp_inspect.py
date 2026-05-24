import json

with open('persist/knowledge_graph.json') as f:
    data = json.load(f)

print(f"Type: {type(data).__name__}")
if isinstance(data, dict):
    keys = list(data.keys())[:3]
    for k in keys:
        print(f"  {k}: {json.dumps(data[k], default=str)[:200]}")
    print(f"Total: {len(data)} entries")
elif isinstance(data, list):
    for item in data[:3]:
        print(f"  {json.dumps(item, default=str)[:200]}")
    print(f"Total: {len(data)} entries")