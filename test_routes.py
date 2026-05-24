from web.app import create_app
app = create_app()
dupes = {}
for rule in app.url_map.iter_rules():
    key = (rule.rule, tuple(sorted(rule.methods - {'OPTIONS','HEAD'})))
    dupes.setdefault(key, []).append(rule.endpoint)
for key, endpoints in sorted(dupes.items()):
    if len(endpoints) > 1:
        print(f'DUPLICATE: {key[0]} methods={key[1]} endpoints={endpoints}')
print('--- Total routes:', sum(1 for _ in app.url_map.iter_rules()))