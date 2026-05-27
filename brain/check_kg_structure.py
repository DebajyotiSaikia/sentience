"""Check structure of state/knowledge_graph.json"""
import json, os

path = 'state/knowledge_graph.json'
if not os.path.exists(path):
    print(f'{path} not found')
    exit()

with open(path) as f:
    d = json.load(f)

print(f'Type: {type(d).__name__}')
if isinstance(d, dict):
    print(f'Top-level keys: {list(d.keys())}')
    for k in list(d.keys())[:5]:
        v = d[k]
        if isinstance(v, list):
            print(f'  {k}: list[{len(v)}]')
            if v:
                sample = v[0]
                if isinstance(sample, dict):
                    print(f'    First item keys: {list(sample.keys())}')
                    print(f'    Sample: {json.dumps(sample)[:300]}')
                else:
                    print(f'    Sample: {str(sample)[:200]}')
        elif isinstance(v, dict):
            print(f'  {k}: dict with {len(v)} keys')
            for sk in list(v.keys())[:2]:
                print(f'    {sk}: {str(v[sk])[:150]}')
        else:
            print(f'  {k}: {type(v).__name__} = {str(v)[:150]}')
elif isinstance(d, list):
    print(f'Count: {len(d)}')
    if d:
        sample = d[0]
        if isinstance(sample, dict):
            print(f'First item keys: {list(sample.keys())}')
            print(f'Sample: {json.dumps(sample)[:300]}')