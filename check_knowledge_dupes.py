import sys
sys.path.insert(0, '.')
from web.app import create_app
from collections import defaultdict

app = create_app()

# Group routes by blueprint
bp_routes = defaultdict(list)
route_map = defaultdict(list)

for rule in app.url_map.iter_rules():
    if rule.endpoint != 'static':
        bp = rule.endpoint.split('.')[0] if '.' in rule.endpoint else 'root'
        bp_routes[bp].append((rule.rule, rule.endpoint))
        route_map[rule.rule].append(rule.endpoint)

# Focus on conflicting blueprints
focus = ['knowledge_api', 'knowledge_hub', 'knowledge_explorer', 'search']
for bp in focus:
    routes = bp_routes.get(bp, [])
    print(f"\n=== {bp} ({len(routes)} routes) ===")
    for route, endpoint in sorted(routes):
        others = [e for e in route_map[route] if e != endpoint]
        tag = " [DUP]" if others else " [UNIQUE]"
        print(f"  {route} -> {endpoint}{tag}")
        if others:
            print(f"    also: {others}")