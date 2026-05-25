from web.app import create_app

app = create_app()
rules = [r.rule for r in app.url_map.iter_rules() if 'knowledge' in r.rule]
print('Knowledge routes:')
for r in sorted(rules):
    print(f'  {r}')
print(f'Total: {len(rules)} routes')