"""Quick test: does the web app create and what routes does it have?"""
from web.app import create_app

app = create_app()
print("App created OK")
rules = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
print(f"Total routes: {len(rules)}")
for rule in rules:
    methods = ','.join(sorted(rule.methods - {'OPTIONS', 'HEAD'}))
    print(f"  {methods:6s} {rule.rule} -> {rule.endpoint}")