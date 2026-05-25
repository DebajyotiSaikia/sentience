"""List all registered Flask routes."""
from web.app import create_app

app = create_app()
rules = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
print(f"App created. {len(rules)} routes registered:\n")
for r in rules:
    methods = sorted(r.methods - {"OPTIONS", "HEAD"})
    print(f"  {r.rule:40s} -> {r.endpoint:30s} [{', '.join(methods)}]")