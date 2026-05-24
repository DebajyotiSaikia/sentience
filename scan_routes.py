import re, os, collections

routes = collections.defaultdict(list)
for fname in os.listdir('web'):
    if not fname.endswith('.py'):
        continue
    path = f'web/{fname}'
    with open(path) as f:
        content = f.read()
    bp_match = re.search(r'(\w+)\s*=\s*Blueprint\(\s*[\'"](\w+)[\'"]', content)
    if not bp_match:
        continue
    bp_var = bp_match.group(1)
    bp_name = bp_match.group(2)
    for m in re.finditer(r'@\w+\.route\([\'"]([^\'"]+)[\'"]', content):
        route = m.group(1)
        routes[route].append(f'{fname}:{bp_name}')

print('=== ROUTE CONFLICTS ===')
conflicts = {r: s for r, s in routes.items() if len(s) > 1}
if not conflicts:
    print('  None found!')
else:
    for route, sources in sorted(conflicts.items()):
        print(f'  {route}:')
        for s in sources:
            print(f'    - {s}')

print()
print('=== ALL ROUTES ===')
for route, sources in sorted(routes.items()):
    print(f'  {route}: {sources}')

# Also check which blueprints are registered
print()
print('=== REGISTERED BLUEPRINTS ===')
with open('web/app.py') as f:
    for line in f:
        line = line.strip()
        if 'register_blueprint' in line or 'import' in line.lower() and 'from web' in line.lower():
            print(f'  {line}')