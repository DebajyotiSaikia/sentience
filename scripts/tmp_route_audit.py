from web.app import create_app
app = create_app()
routes = []
for rule in app.url_map.iter_rules():
    if rule.endpoint != 'static':
        methods = list(rule.methods - {'HEAD', 'OPTIONS'})
        routes.append((rule.rule, rule.endpoint, methods))
routes.sort()
print(f"{'METHOD':6s} {'PATH':50s} ENDPOINT")
print("-" * 80)
for path, endpoint, methods in routes:
    m = methods[0] if methods else 'GET'
    print(f"{m:6s} {path:50s} {endpoint}")
print(f"\nTotal routes: {len(routes)}")