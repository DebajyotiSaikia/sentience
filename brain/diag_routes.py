"""Diagnostic: list all registered Flask routes."""
import sys
sys.path.insert(0, '.')
from web.app import create_app

app = create_app()
print("=== ALL REGISTERED ROUTES ===")
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    methods = rule.methods - {'OPTIONS', 'HEAD'}
    print(f"  {', '.join(sorted(methods)):8s}  {rule.rule}")

print(f"\n=== TOTAL: {len(list(app.url_map.iter_rules()))} rules ===")