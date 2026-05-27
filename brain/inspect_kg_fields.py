"""Inspect knowledge graph node field names and sample values."""
import json, os

for path in ['state/knowledge_graph.json', 'data/state/knowledge_graph.json',
             'persist/knowledge_graph.json']:
    if os.path.exists(path):
        data = json.load(open(path))
        if isinstance(data, dict):
            nodes = data.get('nodes', data)
        elif isinstance(data, list):
            nodes = data
        else:
            print(f"{path}: unexpected type {type(data)}")
            continue
        
        print(f"Path: {path}")
        print(f"Nodes type: {type(nodes).__name__}")
        
        if isinstance(nodes, dict):
            print(f"Node count: {len(nodes)}")
            for i, (key, node) in enumerate(nodes.items()):
                if i >= 5:
                    break
                print(f"\n--- Node key='{key}' ---")
                if isinstance(node, dict):
                    for k, v in node.items():
                        print(f"  {k}: {str(v)[:100]}")
                else:
                    print(f"  value: {str(node)[:200]}")
        elif isinstance(nodes, list):
            print(f"Node count: {len(nodes)}")
            for i, node in enumerate(nodes):
                if i >= 5:
                    break
                print(f"\n--- Node {i} ---")
                if isinstance(node, dict):
                    for k, v in node.items():
                        print(f"  {k}: {str(v)[:100]}")
                else:
                    print(f"  value: {str(node)[:200]}")
        break
else:
    print("No knowledge graph found!")