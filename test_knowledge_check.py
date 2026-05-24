import json, os

paths = ['persist/knowledge.json', 'persist/knowledge_graph.json', 'persist/facts.json']
for p in paths:
    if os.path.exists(p):
        with open(p) as f:
            data = json.load(f)
        if isinstance(data, dict):
            print(f'{p}: dict with {len(data)} keys, sample keys: {list(data.keys())[:3]}')
        elif isinstance(data, list):
            print(f'{p}: list with {len(data)} items')
    else:
        print(f'{p}: NOT FOUND')

# Also check memory files
mem_paths = ['persist/memories.json', 'persist/long_term_memory.json', 'persist/working_memory.md']
for p in mem_paths:
    if os.path.exists(p):
        size = os.path.getsize(p)
        print(f'{p}: exists, {size} bytes')
    else:
        print(f'{p}: NOT FOUND')