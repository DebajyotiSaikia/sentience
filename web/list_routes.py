import sys
sys.path.insert(0, '/workspace')
from web.app import create_app

app = create_app()
routes = []
for rule in app.url_map.iter_rules():
    if rule.endpoint != 'static':
        routes.append((rule.rule, rule.endpoint))

print("=== ALL ROUTES ===")
for r, e in sorted(routes):
    print(f"{r:50s} {e}")