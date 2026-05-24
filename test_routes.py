import sys
sys.path.insert(0, '.')
from web.app import create_app
from collections import defaultdict

app = create_app()
routes = defaultdict(list)
for rule in app.url_map.iter_rules():
    if rule.endpoint != 'static':
        routes[rule.rule].append(rule.endpoint)

dupes = {r: eps for r, eps in routes.items() if len(eps) > 1}
for r, eps in sorted(dupes.items()):
    print(f'{r}: {eps}')

if not dupes:
    print('No duplicates found!')
else:
    print(f'\nTotal duplicate routes: {len(dupes)}')