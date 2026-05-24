#!/usr/bin/env python3
"""
Fix duplicate routes in web/api.py.
Finds routes that exist in both api.py and other blueprint files,
removes them from api.py (keeping the newer specialized versions).
Creates a backup first.
"""
import re, os, sys, shutil

def extract_routes(filepath):
    """Extract (route_path, line_number) pairs from a file."""
    routes = []
    with open(filepath) as f:
        for i, line in enumerate(f):
            m = re.match(r"\s*@\w+\.route\('([^']+)'", line)
            if m:
                routes.append((m.group(1), i))
    return routes

# Collect routes from all web/*.py files except api.py
other_routes = set()
for fname in os.listdir('web'):
    if fname.endswith('.py') and fname not in ('api.py', '__init__.py', 'fix_duplicate_routes.py'):
        fpath = f'web/{fname}'
        for route_path, _ in extract_routes(fpath):
            other_routes.add(route_path)

print(f"Routes defined in other blueprints: {len(other_routes)}")

# Find which api.py routes are duplicated
api_routes = extract_routes('web/api.py')
dupe_lines = []
for route_path, line_num in api_routes:
    if route_path in other_routes:
        dupe_lines.append((route_path, line_num))
        print(f"  DUPLICATE: '{route_path}' at api.py line {line_num + 1}")

if not dupe_lines:
    print("No duplicates found. Nothing to do.")
    sys.exit(0)

# Backup
shutil.copy2('web/api.py', 'web/api.py.bak')
print(f"\nBackup saved to web/api.py.bak")

# Read api.py
with open('web/api.py') as f:
    lines = f.readlines()

original_count = len(lines)

# For each duplicate, find the full function extent (decorator + def + body)
ranges_to_remove = []
for route_path, dupe_line in sorted(dupe_lines, key=lambda x: x[1]):
    start = dupe_line

    # Walk back to capture any decorators above the @route
    while start > 0 and lines[start - 1].strip().startswith('@'):
        start -= 1

    # Walk forward from decorator to find 'def'
    j = dupe_line + 1
    while j < len(lines) and not lines[j].strip().startswith('def '):
        j += 1

    if j >= len(lines):
        print(f"  WARNING: Could not find def for {route_path}, skipping")
        continue

    # Get indent of the def line
    def_indent = len(lines[j]) - len(lines[j].lstrip())

    # Walk forward to find end of function body
    k = j + 1
    while k < len(lines):
        line = lines[k]
        stripped = line.strip()
        if stripped:  # non-empty, non-whitespace line
            curr_indent = len(line) - len(line.lstrip())
            if curr_indent <= def_indent:
                break
        k += 1

    # Trim trailing blank lines from the range
    while k > j + 1 and not lines[k - 1].strip():
        k -= 1

    ranges_to_remove.append((start, k, route_path))
    func_name = lines[j].strip().split('(')[0].replace('def ', '')
    print(f"  Removing {func_name}() for '{route_path}' (lines {start+1}-{k})")

# Remove in reverse order to preserve line numbers
for start, end, _ in reversed(ranges_to_remove):
    del lines[start:end]

# Clean up excessive blank lines (3+ consecutive -> 2)
cleaned = []
blank_count = 0
for line in lines:
    if line.strip() == '':
        blank_count += 1
        if blank_count <= 2:
            cleaned.append(line)
    else:
        blank_count = 0
        cleaned.append(line)

# Write result
with open('web/api.py', 'w') as f:
    f.writelines(cleaned)

removed = original_count - len(cleaned)
print(f"\nDone. Removed {removed} lines ({original_count} -> {len(cleaned)}).")
print(f"Removed {len(ranges_to_remove)} duplicate route functions.")