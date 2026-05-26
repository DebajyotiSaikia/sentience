"""Diagnose why _load_knowledge() returns 0 facts."""
import json
import os

path = 'brain/knowledge.json'
if not os.path.exists(path):
    print("File does not exist!")
else:
    with open(path) as f:
        data = json.load(f)
    print(f"Type: {type(data).__name__}")
    if isinstance(data, dict):
        print(f"Keys: {list(data.keys())[:10]}")
        if 'nodes' in data:
            nodes = data['nodes']
            print(f"Nodes type: {type(nodes).__name__}, count: {len(nodes)}")
            if isinstance(nodes, dict) and nodes:
                first_key = list(nodes.keys())[0]
                print(f"First node key: {first_key}")
                print(f"First node val: {nodes[first_key]}")
        else:
            print("No 'nodes' key — showing first 3 items:")
            for i, (k, v) in enumerate(data.items()):
                if i >= 3:
                    break
                print(f"  {k}: {str(v)[:200]}")
    elif isinstance(data, list):
        print(f"List length: {len(data)}")
        if data:
            print(f"First item: {data[0]}")

# Now test the actual _load_knowledge function
print("\n--- Testing _load_knowledge() ---")
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web.knowledge_live import _load_knowledge
result = _load_knowledge()
print(f"_load_knowledge() returned: type={type(result).__name__}, len={len(result)}")
if result:
    first = list(result.items())[0] if isinstance(result, dict) else result[0]
    print(f"First item: {first}")