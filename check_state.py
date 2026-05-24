import json, os

files = [
    'state/emotional_state.json',
    'state/identity.json', 
    'state/survival_goals.json',
    'state/knowledge_graph.json',
    'state/memories.json'
]

for f in files:
    if os.path.exists(f):
        with open(f) as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            print(f"{f}: keys={list(data.keys())[:10]}")
            if 'survival' in f:
                for k, v in data.items():
                    print(f"  {k}: {type(v).__name__} = {repr(v)[:120]}")
        elif isinstance(data, list):
            print(f"{f}: list[{len(data)}]")
        else:
            print(f"{f}: {type(data).__name__}")
    else:
        print(f"{f}: MISSING")