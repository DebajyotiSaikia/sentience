import sys
sys.path.insert(0, '.')
from web.app import create_app
from collections import defaultdict

app = create_app()

# Find all user_api endpoints
user_api_routes = []
all_routes = defaultdict(list)

for rule in app.url_map.iter_rules():
    if rule.endpoint != 'static':
        all_routes[rule.rule].append(rule.endpoint)
        if rule.endpoint.startswith('user_api.'):
            user_api_routes.append((rule.rule, rule.endpoint))

print("=== All user_api routes ===")
for route, endpoint in sorted(user_api_routes):
    others = [e for e in all_routes[route] if e != endpoint]
    status = "DUPLICATE" if others else "UNIQUE"
    print(f"  {status}: {route} -> {endpoint}")
    if others:
        print(f"         also served by: {others}")

unique = [(r, e) for r, e in user_api_routes if len(all_routes[r]) == 1]
print(f"\nUnique user_api routes: {len(unique)}")
print(f"Duplicate user_api routes: {len(user_api_routes) - len(unique)}")