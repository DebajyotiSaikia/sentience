"""Check where knowledge facts actually live and their structure."""
import json, os

path = 'persist/knowledge_facts.json'
if os.path.exists(path):
    with open(path) as f:
        d = json.load(f)
    print(f'Type: {type(d).__name__}')
    if isinstance(d, list):
        print(f'Count: {len(d)}')
        for item in d[:5]:
            if isinstance(item, dict):
                print(f'  Keys: {list(item.keys())}')
                print(f'  Sample: {json.dumps(item)[:200]}')
            else:
                print(f'  Item: {str(item)[:200]}')
    elif isinstance(d, dict):
        print(f'Keys: {list(d.keys())}')
        for k in list(d.keys())[:3]:
            v = d[k]
            print(f'  {k}: {type(v).__name__} = {str(v)[:100]}')
else:
    print(f'{path} not found')

# Check all knowledge-related files in persist/
if os.path.isdir('persist'):
    files = sorted([f for f in os.listdir('persist') if 'know' in f.lower() or 'fact' in f.lower()])
    print(f'\nKnowledge-related files in persist/: {files}')
    
    # Also check for knowledge_graph anywhere
    for root, dirs, fnames in os.walk('.'):
        for fn in fnames:
            if 'knowledge_graph' in fn:
                full = os.path.join(root, fn)
                size = os.path.getsize(full)
                print(f'Found knowledge_graph file: {full} ({size} bytes)')