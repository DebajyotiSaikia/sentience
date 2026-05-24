from web.app import create_app

app = create_app()
rules = sorted(set(r.rule for r in app.url_map.iter_rules()))
for r in rules:
    print(r)