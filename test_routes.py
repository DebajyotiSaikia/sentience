from web.app import create_app
app = create_app()
rules = sorted([
    (r.rule, list(r.methods - {'OPTIONS','HEAD'}))
    for r in app.url_map.iter_rules()
    if not r.rule.startswith('/static')
])
for rule, methods in rules:
    m = methods[0] if methods else 'GET'
    print(f'{m:6s} {rule}')