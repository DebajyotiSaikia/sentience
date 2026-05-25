from web.app import create_app
app = create_app()
with app.app_context():
    rules = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
    for rule in rules:
        if 'static' not in rule.rule and 'GET' in rule.methods:
            print(f'{rule.rule:45s} -> {rule.endpoint}')