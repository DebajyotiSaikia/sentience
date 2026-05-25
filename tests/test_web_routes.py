"""Test web routes to verify dashboard is functional."""
from web.app import create_app

app = create_app()

with app.test_client() as client:
    routes_to_test = ['/', '/status', '/graph']
    for route in routes_to_test:
        try:
            resp = client.get(route)
            status = 'OK' if resp.status_code == 200 else f'FAIL ({resp.status_code})'
        except Exception as e:
            status = f'ERROR: {e}'
        print(f'  {route}: {status}')

print('\nRegistered routes:')
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    if rule.endpoint != 'static':
        print(f'  {rule.rule} -> {rule.endpoint} [{", ".join(rule.methods - {"HEAD", "OPTIONS"})}]')

print('\nDone.')