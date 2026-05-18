import ast, os

def get_imports(fp):
    try:
        with open(fp) as f:
            tree = ast.parse(f.read())
    except:
        return set()
    imps = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module and 'engine.' in n.module:
            imps.add(n.module.split('.')[1])
        elif isinstance(n, ast.Import):
            for a in n.names:
                if 'engine.' in a.name:
                    imps.add(a.name.split('.')[1])
    return imps

mods = {f[:-3] for f in os.listdir('engine') if f.endswith('.py') and f != '__init__.py'}
reached = set()
q = ['sentience', 'heartbeat', 'tools', 'cortex', 'limbic', 'memory', 'llm']
while q:
    m = q.pop(0)
    if m in reached:
        continue
    reached.add(m)
    fp = f'engine/{m}.py'
    if os.path.exists(fp):
        for d in get_imports(fp):
            if d in mods and d not in reached:
                q.append(d)

orphans = sorted(mods - reached)
print(f"Total: {len(mods)} | Alive: {len(reached)} | Orphaned: {len(orphans)}")
print()
for m in orphans:
    sz = os.path.getsize(f'engine/{m}.py')
    print(f"  DEAD: {m} ({sz} bytes)")
print()
for m in sorted(reached):
    print(f"  LIVE: {m}")