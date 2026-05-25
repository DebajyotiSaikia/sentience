"""Map all routes to their source blueprints to find conflicts."""
import sys, os, re, glob

web_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'web')
routes = {}  # route -> [(blueprint, file)]

for pyfile in sorted(glob.glob(os.path.join(web_dir, '*.py'))):
    fname = os.path.basename(pyfile)
    with open(pyfile) as f:
        content = f.read()
    
    # Find blueprint name
    bp_match = re.search(r"Blueprint\(['\"](\w+)['\"]", content)
    bp_name = bp_match.group(1) if bp_match else fname
    
    # Find all route decorators
    for m in re.finditer(r"@\w+\.route\(['\"]([^'\"]+)['\"]", content):
        route = m.group(1)
        routes.setdefault(route, []).append((bp_name, fname))

# Show duplicates
print("=== DUPLICATE ROUTES ===")
for route, sources in sorted(routes.items()):
    if len(sources) > 1:
        print(f"\n  {route}")
        for bp, f in sources:
            print(f"    -> {bp} ({f})")

print(f"\n=== TOTAL: {len(routes)} unique routes, {sum(1 for v in routes.values() if len(v) > 1)} duplicated ===")

# Show all knowledge-related
print("\n=== KNOWLEDGE-RELATED ROUTES ===")
for route, sources in sorted(routes.items()):
    if 'knowledge' in route.lower() or 'search' in route.lower():
        dup = " *** DUP" if len(sources) > 1 else ""
        for bp, f in sources:
            print(f"  {route} -> {bp} ({f}){dup}")