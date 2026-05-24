"""Check data shapes so I know what state_sync needs to produce."""
import json, os

# Check brain data shapes
for f in ['knowledge.json', 'narrative.json', 'temporal_log.json']:
    path = f'brain/{f}'
    if os.path.exists(path):
        with open(path) as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            print(f'{f}: dict with keys {list(data.keys())[:5]}')
        elif isinstance(data, list):
            print(f'{f}: list with {len(data)} items')
            if data:
                item = data[0]
                if isinstance(item, dict):
                    print(f'  first item keys: {list(item.keys())[:6]}')
    else:
        print(f'{f}: NOT FOUND')

# Check soul.json for plans
if os.path.exists('soul.json'):
    with open('soul.json') as fh:
        soul = json.load(fh)
    if 'plans' in soul:
        print(f'soul.json plans: {len(soul["plans"])} plans')
        if soul['plans']:
            print(f'  first plan keys: {list(soul["plans"][0].keys())[:6]}')
    if 'goals' in soul:
        print(f'soul.json goals: {list(soul["goals"].keys())[:5]}')

# Check what state/ currently has
print('\n--- state/ directory ---')
if os.path.exists('state'):
    for f in sorted(os.listdir('state')):
        path = f'state/{f}'
        size = os.path.getsize(path)
        print(f'  {f}: {size} bytes')
        if size > 0 and f.endswith('.json'):
            with open(path) as fh:
                d = json.load(fh)
            if isinstance(d, dict):
                print(f'    keys: {list(d.keys())[:5]}')
            elif isinstance(d, list):
                print(f'    list with {len(d)} items')
else:
    print('  state/ does not exist')

# Check what API expects
print('\n--- API endpoints expecting state/ ---')
if os.path.exists('web/api.py'):
    with open('web/api.py') as fh:
        for line in fh:
            if 'state/' in line:
                print(f'  {line.strip()}')