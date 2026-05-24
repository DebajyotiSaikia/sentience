from web.app import create_app
app = create_app()
for r in app.url_map.iter_rules():
    if 'knowledge' in r.rule:
        print(f'  {r.rule} -> {r.endpoint} [{r.methods}]')
print('Done.')