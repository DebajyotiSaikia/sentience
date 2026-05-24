import json, os

paths = {
    'brain/knowledge': 'brain/knowledge.json',
    'brain/plans': 'brain/plans.json',
    'state/memories': 'state/memories.json',
    'state/plans': 'state/plans.json',
}

for label, path in paths.items():
    full = os.path.join('/workspace', path)
    print(f'\n{"="*60}')
    print(f'  {label} — {full}')
    print(f'{"="*60}')
    if not os.path.exists(full):
        print('  FILE NOT FOUND')
        continue
    with open(full) as f:
        data = json.load(f)
    print(f'  Type: {type(data).__name__}, Size: {os.path.getsize(full)} bytes')
    
    if isinstance(data, dict):
        keys = list(data.keys())
        print(f'  Keys ({len(keys)}): {keys[:8]}{"..." if len(keys) > 8 else ""}')
        for k in keys[:3]:
            v = data[k]
            if isinstance(v, dict):
                print(f'    [{k}] dict keys: {list(v.keys())[:6]}')
            elif isinstance(v, list):
                print(f'    [{k}] list len: {len(v)}')
                if v:
                    first = v[0]
                    if isinstance(first, dict):
                        print(f'      First item keys: {list(first.keys())[:6]}')
                    else:
                        print(f'      First item: {str(first)[:100]}')
            elif isinstance(v, str):
                print(f'    [{k}] str: {v[:100]}')
            else:
                print(f'    [{k}] {type(v).__name__}: {str(v)[:100]}')
    elif isinstance(data, list):
        print(f'  Length: {len(data)}')
        if data:
            first = data[0]
            if isinstance(first, dict):
                print(f'  First item keys: {list(first.keys())[:8]}')
                for k in list(first.keys())[:4]:
                    print(f'    {k}: {str(first[k])[:80]}')
            else:
                print(f'  First item: {str(first)[:100]}')

# Also check for any other interesting data
print(f'\n{"="*60}')
print('  Other JSON files in brain/ and state/')
print(f'{"="*60}')
for d in ['brain', 'state']:
    full_d = os.path.join('/workspace', d)
    if os.path.isdir(full_d):
        for f in sorted(os.listdir(full_d)):
            fp = os.path.join(full_d, f)
            size = os.path.getsize(fp) if os.path.isfile(fp) else 'DIR'
            print(f'  {d}/{f} — {size}')