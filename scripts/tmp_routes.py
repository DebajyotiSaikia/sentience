from web.app import create_app
app = create_app()

with app.app_context():
    rules = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
    for rule in rules:
        if not rule.rule.startswith('/static'):
            methods = list(rule.methods - {"OPTIONS", "HEAD"})
            print(f"{rule.rule:40s} {methods}")