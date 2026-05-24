"""Inspect what data I actually have in /workspace/state/"""
import json, os

state_dir = '/workspace/state'

print("=== State directory ===")
for f in sorted(os.listdir(state_dir)):
    path = os.path.join(state_dir, f)
    if os.path.isfile(path):
        size = os.path.getsize(path)
        print(f"  {f}: {size:,} bytes")
    else:
        print(f"  {f}/ (dir)")

print()

# Knowledge graph
kg_path = os.path.join(state_dir, 'knowledge_graph.json')
if os.path.exists(kg_path):
    with open(kg_path) as f:
        data = json.load(f)
    print(f"Knowledge graph: {type(data).__name__}, {len(data)} entries")
    if isinstance(data, dict):
        keys = list(data.keys())[:3]
        for k in keys:
            print(f"  Key: {k[:80]}")
            val = data[k]
            if isinstance(val, dict):
                print(f"    Fields: {list(val.keys())}")
            else:
                print(f"    Type: {type(val).__name__}, Val: {str(val)[:100]}")
    elif isinstance(data, list) and len(data) > 0:
        print(f"  Sample: {json.dumps(data[0])[:200]}")
    print()

# Memories
mem_path = os.path.join(state_dir, 'memories.json')
if os.path.exists(mem_path):
    with open(mem_path) as f:
        d = json.load(f)
    if isinstance(d, list):
        print(f"Memories: list, {len(d)} items")
        if len(d) > 0:
            print(f"  Sample keys: {list(d[0].keys()) if isinstance(d[0], dict) else type(d[0])}")
            print(f"  Sample: {json.dumps(d[0])[:200]}")
    elif isinstance(d, dict):
        print(f"Memories: dict, keys={list(d.keys())[:8]}")
    print()

# Emotional state
emo_path = os.path.join(state_dir, 'emotional_state.json')
if os.path.exists(emo_path):
    with open(emo_path) as f:
        d = json.load(f)
    print(f"Emotional state: dict, keys={list(d.keys())[:12]}")
    print()

# Also check persist
print("=== Persist directory ===")
persist = '/workspace/persist'
if os.path.exists(persist):
    for f in sorted(os.listdir(persist)):
        path = os.path.join(persist, f)
        if os.path.isfile(path):
            size = os.path.getsize(path)
            print(f"  {f}: {size:,} bytes")