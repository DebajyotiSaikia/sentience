import json, os

# Check what data files exist that search might use
paths = [
    'persist/knowledge.json',
    'persist/knowledge_graph.json',
    'persist/facts.json',
    'persist/memories.json',
    'persist/episodic_memory.json',
]
for p in paths:
    if os.path.exists(p):
        size = os.path.getsize(p)
        with open(p) as f:
            data = json.load(f)
        if isinstance(data, list):
            print(f'{p}: {size}B, list[{len(data)}]')
            if data:
                print(f'  sample: {str(data[0])[:120]}')
        elif isinstance(data, dict):
            keys = list(data.keys())[:5]
            print(f'{p}: {size}B, dict keys={keys}')
            if keys:
                print(f'  sample[{keys[0]}]: {str(data[keys[0]])[:120]}')
    else:
        print(f'{p}: MISSING')

print('\n--- Now checking what search() actually does ---')
from web import knowledge_search as ks
import inspect
src = inspect.getsource(ks.search)
# Just show first 40 lines
lines = src.split('\n')[:40]
for i, line in enumerate(lines):
    print(f'{i}: {line}')