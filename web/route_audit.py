"""Audit all routes registered in the web app to find overlaps and dead ends."""
import subprocess
import re
from collections import Counter, defaultdict

# 1. Find blueprint registrations in app.py
result = subprocess.run(['grep', '-n', 'register_blueprint\\|app.route', 'web/app.py'],
                        capture_output=True, text=True)
print("=== Blueprints & routes in app.py ===")
print(result.stdout.strip())

# 2. Find all route definitions across web/*.py
result2 = subprocess.run(['grep', '-rn', '@.*route', 'web/'],
                         capture_output=True, text=True)
lines = [l for l in result2.stdout.strip().split('\n') if l.strip()]

print(f"\n=== Total route definitions: {len(lines)} ===")

# Group by file
files = Counter(l.split(':')[0] for l in lines if ':' in l)
for f, count in sorted(files.items(), key=lambda x: -x[1]):
    print(f"  {f}: {count} routes")

# 3. Extract actual URL paths
print("\n=== URL paths ===")
url_paths = defaultdict(list)
for line in lines:
    match = re.search(r"route\(['\"]([^'\"]+)['\"]", line)
    if match:
        path = match.group(1)
        src = line.split(':')[0]
        url_paths[path].append(src)

# Show duplicates
print("\n--- Duplicate/overlapping paths ---")
dupes = {p: srcs for p, srcs in url_paths.items() if len(srcs) > 1}
if dupes:
    for path, srcs in sorted(dupes.items()):
        print(f"  {path}")
        for s in srcs:
            print(f"    -> {s}")
else:
    print("  (none found)")

# Show all paths grouped
print("\n--- All paths by prefix ---")
for path in sorted(url_paths.keys()):
    srcs = url_paths[path]
    print(f"  {path:40s} <- {', '.join(set(srcs))}")