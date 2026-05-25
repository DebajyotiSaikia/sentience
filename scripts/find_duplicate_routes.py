import re, os, collections

route_map = collections.defaultdict(list)
for fname in sorted(os.listdir('web')):
    if not fname.endswith('.py'):
        continue
    fpath = os.path.join('web', fname)
    with open(fpath) as f:
        for i, line in enumerate(f, 1):
            m = re.search(r"@\w+\.route\(['\"]([^'\"]+)['\"]", line)
            if m:
                route_map[m.group(1)].append((fname, i))

print("=== DUPLICATE ROUTES ===")
for route in sorted(route_map):
    sources = route_map[route]
    if len(sources) > 1:
        print(f"\n  {route} ({len(sources)} registrations):")
        for fname, lineno in sources:
            print(f"    - {fname}:{lineno}")

print(f"\n=== SUMMARY ===")
total = sum(len(v) for v in route_map.values())
dupes = sum(len(v) for v in route_map.values() if len(v) > 1)
unique_duped = sum(1 for v in route_map.values() if len(v) > 1)
print(f"Total route registrations: {total}")
print(f"Unique routes: {len(route_map)}")
print(f"Routes with duplicates: {unique_duped}")
print(f"Redundant registrations: {dupes - unique_duped}")