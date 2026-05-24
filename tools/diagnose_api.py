"""Diagnose the gap between persist/ data and web/api.py endpoints."""
import os, json, glob

print("=" * 60)
print("PERSIST DIRECTORY CONTENTS")
print("=" * 60)
persist_dir = os.path.join(os.path.dirname(__file__), '..', 'persist')
for f in sorted(glob.glob(os.path.join(persist_dir, '*'))):
    name = os.path.basename(f)
    if os.path.isfile(f):
        size = os.path.getsize(f)
        # Show first 200 chars of JSON files
        preview = ""
        if f.endswith('.json'):
            try:
                with open(f) as fh:
                    data = json.load(fh)
                if isinstance(data, dict):
                    preview = f"  dict with {len(data)} keys: {list(data.keys())[:5]}"
                elif isinstance(data, list):
                    preview = f"  list with {len(data)} items"
            except:
                preview = "  (not valid JSON)"
        print(f"  {name:40s} {size:>8d} bytes{preview}")
    elif os.path.isdir(f):
        count = len(os.listdir(f))
        print(f"  {name + '/':40s} {count} files")

print()
print("=" * 60)
print("WEB/API.PY ROUTE ANALYSIS")
print("=" * 60)
api_path = os.path.join(os.path.dirname(__file__), '..', 'web', 'api.py')
with open(api_path) as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '@' in line and 'route' in line.lower():
        print(f"  Line {i+1}: {line.strip()}")
    if 'def ' in line and '(' in line:
        # Show function and next few lines for context
        func_preview = line.strip()
        # Look for return statements nearby
        for j in range(i+1, min(i+10, len(lines))):
            if 'return' in lines[j] or 'jsonify' in lines[j]:
                func_preview += f" -> {lines[j].strip()}"
                break
        print(f"  Line {i+1}: {func_preview}")

print()
print("=" * 60)
print("AVAILABLE ENGINE MODULES")
print("=" * 60)
engine_dir = os.path.join(os.path.dirname(__file__), '..', 'engine')
for f in sorted(os.listdir(engine_dir)):
    if f.endswith('.py'):
        print(f"  engine/{f}")