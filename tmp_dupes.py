from web.app import create_app
from collections import Counter
app = create_app()

paths = []
blueprints = set()
for rule in app.url_map.iter_rules():
    if 'static' in rule.rule:
        continue
    paths.append(rule.rule)
    bp = rule.endpoint.split('.')[0] if '.' in rule.endpoint else '(root)'
    blueprints.add(bp)

print(f"Total blueprints: {len(blueprints)}")
print(f"Total routes: {len(paths)}")
print(f"\nBlueprints: {', '.join(sorted(blueprints))}")

dupes = {p: c for p, c in Counter(paths).items() if c > 1}
print(f"\n=== DUPLICATE PATHS ({len(dupes)}) ===")
for p, c in sorted(dupes.items()):
    # Find which endpoints serve this path
    endpoints = [r.endpoint for r in app.url_map.iter_rules() if r.rule == p]
    print(f"  {p} ({c}x): {endpoints}")

# Find semantically similar paths
print("\n=== SIMILAR PATHS ===")
groups = {}
for p in sorted(set(paths)):
    key = p.split('/')[-1].replace('-', '_') if '/' in p else p
    if key not in groups:
        groups[key] = []
    groups[key].append(p)
for key, ps in sorted(groups.items()):
    if len(ps) > 1:
        print(f"  '{key}': {ps}")