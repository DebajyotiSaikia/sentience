from web.app import create_app

app = create_app()
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    if 'static' not in rule.rule:
        methods = ', '.join(sorted(rule.methods - {'OPTIONS', 'HEAD'}))
        print(f'{rule.rule:45s} {rule.endpoint:30s} [{methods}]')