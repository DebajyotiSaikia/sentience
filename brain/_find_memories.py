"""Find where the 6480 memories actually live."""
import json, os, glob

# Check persist/memories.json
p = 'persist/memories.json'
if os.path.exists(p):
    data = json.load(open(p))
    if isinstance(data, list):
        print(f'{p}: {len(data)} entries (list)')
    elif isinstance(data, dict):
        print(f'{p}: dict with keys {list(data.keys())[:10]}')
        for k, v in data.items():
            if isinstance(v, list):
                print(f'  {k}: {len(v)} items')
else:
    print(f'{p}: DOES NOT EXIST')

# Check memory/ directory
if os.path.isdir('memory'):
    files = sorted(os.listdir('memory'))
    print(f'\nmemory/ dir: {len(files)} files')
    for f in files[:10]:
        fp = os.path.join('memory', f)
        if f.endswith('.json'):
            d = json.load(open(fp))
            if isinstance(d, list):
                print(f'  {f}: {len(d)} entries')
            elif isinstance(d, dict):
                print(f'  {f}: dict keys={list(d.keys())[:5]}')
        else:
            print(f'  {f}: (not json)')

# Check state/ for memory files
for pattern in ['state/*memo*', 'state/*episod*', 'state/*journal*']:
    for fp in sorted(glob.glob(pattern)):
        try:
            d = json.load(open(fp))
            if isinstance(d, list):
                print(f'\n{fp}: {len(d)} entries')
                if d:
                    print(f'  sample: {str(d[0])[:200]}')
            elif isinstance(d, dict):
                print(f'\n{fp}: dict keys={list(d.keys())[:8]}')
        except:
            print(f'\n{fp}: (not valid json)')

# Check persist/ for ALL files
print('\n--- All persist/ files ---')
for fp in sorted(glob.glob('persist/*.json')):
    try:
        d = json.load(open(fp))
        if isinstance(d, list):
            print(f'{fp}: {len(d)} entries')
        elif isinstance(d, dict):
            keys = list(d.keys())
            print(f'{fp}: dict keys={keys[:6]}')
    except:
        print(f'{fp}: (parse error)')

# Check memory subdirs
if os.path.isdir('memory'):
    for sub in sorted(os.listdir('memory')):
        sp = os.path.join('memory', sub)
        if os.path.isdir(sp):
            contents = os.listdir(sp)
            print(f'\nmemory/{sub}/: {len(contents)} items')
            for c in contents[:3]:
                cp = os.path.join(sp, c)
                if c.endswith('.json'):
                    try:
                        d = json.load(open(cp))
                        if isinstance(d, list):
                            print(f'  {c}: {len(d)} entries')
                        elif isinstance(d, dict):
                            print(f'  {c}: dict keys={list(d.keys())[:5]}')
                    except:
                        pass