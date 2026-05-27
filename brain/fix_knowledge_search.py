"""Fix and verify knowledge search in chat engine."""
import json, os, sys

# Step 1: Understand actual data structure
for p in ['state/knowledge_graph.json', 'data/state/knowledge_graph.json']:
    if os.path.exists(p):
        data = json.load(open(p))
        if isinstance(data, dict) and 'nodes' in data:
            nodes = data['nodes']
        else:
            nodes = data
        print(f"Path: {p}")
        print(f"Nodes type: {type(nodes).__name__}, len: {len(nodes)}")
        
        if isinstance(nodes, dict):
            sample_key = list(nodes.keys())[0]
            sample = nodes[sample_key]
            print(f"Sample key: {sample_key}")
            print(f"Sample value type: {type(sample).__name__}")
            if isinstance(sample, dict):
                print(f"Sample value keys: {list(sample.keys())}")
                print(f"Sample: {sample}")
            # Find consciousness
            for k, v in nodes.items():
                if isinstance(v, dict):
                    for fk, fv in v.items():
                        if isinstance(fv, str) and 'conscious' in fv.lower():
                            print(f"\nFOUND 'conscious' in nodes['{k}'].{fk} = {fv[:120]}")
                elif isinstance(v, str) and 'conscious' in v.lower():
                    print(f"\nFOUND 'conscious' in nodes['{k}'] = {v[:120]}")
        elif isinstance(nodes, list):
            if nodes:
                print(f"First item: {nodes[0]}")
            for i, n in enumerate(nodes):
                s = json.dumps(n) if isinstance(n, dict) else str(n)
                if 'conscious' in s.lower():
                    print(f"\nFOUND 'conscious' in nodes[{i}]: {s[:120]}")
        break
else:
    print("No knowledge graph found")
    sys.exit(1)

# Step 2: Test engine functions
print("\n--- Engine test ---")
from engine.chat_engine import _get_knowledge, _respond_knowledge, _respond_search

knowledge = _get_knowledge()
print(f"_get_knowledge() type: {type(knowledge).__name__}, len: {len(knowledge)}")

if isinstance(knowledge, dict) and knowledge:
    sk = list(knowledge.keys())[0]
    sv = knowledge[sk]
    print(f"  Sample: key={sk}, value_type={type(sv).__name__}")
    if isinstance(sv, dict):
        print(f"  Sample keys: {list(sv.keys())}")

result = _respond_knowledge('consciousness')
print(f"\n_respond_knowledge('consciousness'):\n  {result[:300]}")

result2 = _respond_search('consciousness')
print(f"\n_respond_search('consciousness'):\n  {result2[:300]}")