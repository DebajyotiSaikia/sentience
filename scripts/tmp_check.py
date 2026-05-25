import json, os

# Check what exists where
for d in ['state', 'brain', 'data', 'persist']:
    p = f'/workspace/{d}'
    if os.path.isdir(p):
        files = [f for f in os.listdir(p) if f.endswith('.json')]
        print(f'{d}/: {len(files)} json files: {files[:8]}')
    else:
        print(f'{d}/: DOES NOT EXIST')

# Check specific files portal might need
targets = [
    'state/emotional_state.json',
    'brain/plans.json', 
    'brain/knowledge.json',
    'brain/identity.json',
    'persist/state.json',
    'persist/plans.json',
    'data/state.json',
]
print('\n--- Portal data availability ---')
for t in targets:
    full = f'/workspace/{t}'
    exists = os.path.exists(full)
    if exists:
        with open(full) as f:
            d = json.load(f)
        print(f'  {t}: EXISTS ({type(d).__name__}, {len(d)} keys/items)')
    else:
        print(f'  {t}: MISSING')