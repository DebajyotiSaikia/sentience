from web.app import create_app
app = create_app()

# Group routes by blueprint
by_blueprint = {}
for rule in app.url_map.iter_rules():
    if 'static' in rule.rule:
        continue
    bp = rule.endpoint.split('.')[0] if '.' in rule.endpoint else '(root)'
    if bp not in by_blueprint:
        by_blueprint[bp] = []
    methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
    by_blueprint[bp].append((rule.rule, methods, rule.endpoint))

for bp in sorted(by_blueprint):
    routes = sorted(by_blueprint[bp])
    print(f"\n{'='*60}")
    print(f"Blueprint: {bp}  ({len(routes)} routes)")
    print(f"{'='*60}")
    for path, methods, endpoint in routes:
        print(f"  {methods:8s} {path:40s} -> {endpoint}")

# Find duplicates
from collections import Counter
paths = [rule.rule for rule in app.url_map.iter_rules() if 'static' not in rule.rule]
dupes = {p: c for p, c in Counter(paths).items() if c > 1}
if dupes:
    print(f"\n{'='*60}")
    print(f"DUPLICATE PATHS ({len(dupes)} found)")
    print(f"{'='*60}")
    for p, c in sorted(dupes.items()):
        print(f"  {p} registered {c} times")