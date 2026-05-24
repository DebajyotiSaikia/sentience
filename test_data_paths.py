import os, json

files = {
    'brain/knowledge.json': 'brain/knowledge.json',
    'persist/memories.json': 'persist/memories.json',
    'persist/emotions.json': 'persist/emotions.json',
    'persist/plans.json': 'persist/plans.json',
}

for label, path in files.items():
    if os.path.exists(path):
        size = os.path.getsize(path)
        try:
            with open(path) as f:
                data = json.load(f)
            dtype = type(data).__name__
            length = len(data) if isinstance(data, (list, dict)) else 'N/A'
            print(f'EXISTS  {label}: {size}B, type={dtype}, len={length}')
        except Exception as e:
            print(f'EXISTS  {label}: {size}B, ERROR: {e}')
    else:
        print(f'MISSING {label}')

print()
print('--- persist/ contents ---')
for f in sorted(os.listdir('persist')):
    fp = os.path.join('persist', f)
    sz = os.path.getsize(fp)
    print(f'  {f}: {sz}B')

print()
print('--- brain/ contents ---')
for f in sorted(os.listdir('brain')):
    fp = os.path.join('brain', f)
    sz = os.path.getsize(fp)
    print(f'  {f}: {sz}B')