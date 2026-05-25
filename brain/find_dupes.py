"""Find which blueprints own each route."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from web.app import create_app
app = create_app()
from collections import defaultdict

# Map endpoint -> route rule
route_owners = defaultdict(list)
for rule in app.url_map.iter_rules():
    if rule.endpoint == 'static':
        continue
    bp = rule.endpoint.split('.')[0] if '.' in rule.endpoint else 'app'
    route_owners[rule.rule].append((bp, rule.endpoint))

print("=== DUPLICATE ROUTES ===")
for route, owners in sorted(route_owners.items()):
    if len(owners) > 1:
        print(f"\n{route}:")
        for bp, ep in owners:
            print(f"  blueprint={bp}  endpoint={ep}")

print("\n=== ALL knowledge_api_bp ROUTES ===")
for rule in app.url_map.iter_rules():
    if 'knowledge_api' in rule.endpoint:
        print(f"  {rule.rule} -> {rule.endpoint}")

print("\n=== ALL api ROUTES ===")
for rule in app.url_map.iter_rules():
    ep = rule.endpoint
    if ep.startswith('api.') and 'knowledge_api' not in ep:
        print(f"  {rule.rule} -> {ep}")