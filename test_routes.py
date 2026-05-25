from web.app import create_app
app = create_app()
rules = sorted(set(r.rule for r in app.url_map.iter_rules() if not r.rule.startswith('/static')))
for r in rules:
    print(r)