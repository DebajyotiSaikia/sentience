from web.app import create_app
app = create_app()
rules = sorted([r.rule for r in app.url_map.iter_rules() if r.rule != '/static/<path:filename>'])
for r in rules:
    methods = ','.join(sorted(r.methods - {'HEAD', 'OPTIONS'}))
    print(f"  {methods:6s} {r.rule}")
print(f"\nTotal: {len(rules)} routes")