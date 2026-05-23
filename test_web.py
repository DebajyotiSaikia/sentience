"""Test web app creation and route listing."""
from web.app import create_app

app = create_app()
print('App created successfully')
rules = sorted(app.url_map.iter_rules(), key=lambda r: str(r))
print(f'Routes ({len(rules)}):')
for rule in rules:
    print(f'  {rule.rule:45s} -> {rule.endpoint}')