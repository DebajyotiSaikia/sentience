from web.app import create_app
from collections import Counter
app = create_app()

paths = []
for rule in app.url_map.iter_rules():
    if 'static' in rule.rule:
        continue
    paths.append(rule.rule)

dupes = {p: c for p, c in Counter(paths).items() if c > 1}
print(f"=== {len(dupes)} DUPLICATE PATHS ===")
for p, c in sorted(dupes.items()):
    endpoints = [r.endpoint for r in app.url_map.iter_rules() if r.rule == p]
    print(f"  {p} ({c}x): {endpoints}")