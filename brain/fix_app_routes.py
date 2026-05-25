"""Remove inline duplicate routes from web/app.py.
These routes are already served by registered blueprints."""
import re

with open('web/app.py', 'r') as f:
    lines = f.readlines()

# Find all @app.route lines and their positions
print("=== All @app.route definitions ===")
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith('@app.route') or stripped.startswith('def ') and i > 0 and lines[i-1].strip().startswith('@app.route'):
        print(f"  L{i+1}: {line.rstrip()}")

# Find blocks to remove: inline route handlers that duplicate blueprint routes
# These are @app.route(...) followed by def func(): followed by body
remove_ranges = []
i = 0
while i < len(lines):
    stripped = lines[i].strip()
    if stripped.startswith('@app.route'):
        # Check if this is a duplicate route we want to remove
        route_match = re.search(r"@app\.route\('([^']+)'", stripped)
        if route_match:
            route_path = route_match.group(1)
            duplicate_routes = [
                '/api/search',
                '/api/knowledge/synthesis',
                '/api/knowledge/clusters', 
                '/api/knowledge/gaps',
                '/api/knowledge/questions',
            ]
            if route_path in duplicate_routes:
                # Find the end of this function block
                start = i
                # Skip decorator line(s)
                j = i + 1
                # Skip to def line
                while j < len(lines) and not lines[j].strip().startswith('def '):
                    j += 1
                if j < len(lines):
                    # Now find end of function body
                    j += 1  # skip def line
                    while j < len(lines):
                        next_stripped = lines[j].strip()
                        # End of function: next non-empty, non-comment line at indent 0
                        if next_stripped and not next_stripped.startswith('#'):
                            # Check indentation
                            indent = len(lines[j]) - len(lines[j].lstrip())
                            if indent == 0 or (indent <= 4 and next_stripped.startswith('@app.route')):
                                break
                        elif next_stripped == '':
                            # blank line - peek ahead
                            if j + 1 < len(lines):
                                peek = lines[j+1]
                                peek_indent = len(peek) - len(peek.lstrip())
                                if peek.strip() and peek_indent == 0:
                                    break
                                elif peek.strip().startswith('@app.route') and peek_indent <= 4:
                                    break
                        j += 1
                    remove_ranges.append((start, j, route_path))
                    print(f"\n  WILL REMOVE: {route_path} (lines {start+1}-{j})")
    i += 1

if not remove_ranges:
    print("\nNo duplicate inline routes found to remove.")
else:
    # Remove in reverse order to preserve line numbers
    remove_ranges.sort(key=lambda x: x[0], reverse=True)
    for start, end, path in remove_ranges:
        del lines[start:end]
    
    with open('web/app.py', 'w') as f:
        f.writelines(lines)
    print(f"\nRemoved {len(remove_ranges)} duplicate route blocks.")
    print(f"New file has {len(lines)} lines.")