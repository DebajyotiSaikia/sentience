from web.app import create_app
app = create_app()
rules = sorted([(r.rule, list(r.methods - {'OPTIONS','HEAD'})) for r in app.url_map.iter_rules() if r.rule != '/static/<path:filename>'])
for rule, methods in rules:
    print(f'{methods[0]:6s} {rule}')