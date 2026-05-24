"""Quick route audit - run once and delete."""
from app import create_app

app = create_app()
routes = sorted(set(r.rule for r in app.url_map.iter_rules() if not r.rule.startswith('/static')))
print(f'Total routes: {len(routes)}')
for r in routes:
    endpoint = None
    for rule in app.url_map.iter_rules():
        if rule.rule == r:
            endpoint = rule.endpoint
            break
    print(f'  {r}  ->  {endpoint}')