from web.app import create_app
app = create_app()
routes = []
for rule in app.url_map.iter_rules():
    if 'static' not in rule.rule:
        routes.append((rule.rule, list(rule.methods - {'HEAD', 'OPTIONS'})))
routes.sort()
print(f"Total routes: {len(routes)}\n")
for r, methods in routes:
    print(f"  {','.join(methods):6s} {r}")