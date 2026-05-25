import sys
sys.path.insert(0, '.')
from collections import defaultdict
from web.app import create_app

app = create_app()

route_map = defaultdict(list)
for rule in app.url_map.iter_rules():
    if rule.endpoint != 'static':
        route_map[rule.rule].append(rule.endpoint)

dupes = {r: eps for r, eps in route_map.items() if len(eps) > 1}

if dupes:
    print("DUPLICATES REMAIN:")
    for route, endpoints in sorted(dupes.items()):
        print(f"  {route} -> {endpoints}")
else:
    print("SUCCESS: No duplicate routes!")

print(f"\nTotal routes: {sum(len(v) for v in route_map.values())}")