"""Diagnostic: show all knowledge-related routes in the Flask app."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web.app import create_app

app = create_app()
routes = []
for rule in app.url_map.iter_rules():
    if 'knowledge' in rule.rule:
        routes.append((rule.rule, rule.endpoint, sorted(rule.methods - {'HEAD', 'OPTIONS'})))
routes.sort()
for r, e, m in routes:
    print(f"{r:50s} {','.join(m):8s} -> {e}")
print(f"\nTotal knowledge routes: {len(routes)}")