"""Find duplicate blueprint registrations in app.py by analyzing the source."""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
app = create_app()

# 1. Show all blueprints grouped by URL prefix
from collections import defaultdict, Counter

by_prefix = defaultdict(list)
for name, bp in app.blueprints.items():
    prefix = bp.url_prefix or '/'
    by_prefix[prefix].append((name, getattr(bp, 'import_name', '?')))

print("=== BLUEPRINTS BY PREFIX ===")
for prefix in sorted(by_prefix):
    bps = by_prefix[prefix]
    marker = "CONFLICT" if len(bps) > 1 else "ok"
    print(f"\n[{marker}] {prefix}:")
    for name, imp in bps:
        print(f"  {name} <- {imp}")

# 2. Show duplicate routes
print("\n=== DUPLICATE ROUTES ===")
route_count = Counter()
route_sources = defaultdict(list)
for rule in app.url_map.iter_rules():
    route_count[rule.rule] += 1
    route_sources[rule.rule].append(rule.endpoint)

for route, count in route_count.most_common():
    if count > 1:
        endpoints = route_sources[route]
        print(f"  {route} ({count}x): {endpoints}")

# 3. Read app.py source and find register_blueprint calls
print("\n=== BLUEPRINT REGISTRATIONS IN app.py ===")
app_path = os.path.join(os.path.dirname(__file__), 'app.py')
with open(app_path) as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if 'register_blueprint' in line or 'Blueprint' in line:
        print(f"  L{i}: {line.rstrip()}")