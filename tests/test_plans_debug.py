import os, json

# Check both known locations
paths = [
    '/workspace/brain/plans.json',
    '/workspace/state/plans.json',
]

for p in paths:
    print(f"\n--- {p} ---")
    if os.path.exists(p):
        try:
            with open(p) as f:
                data = json.load(f)
            if isinstance(data, list):
                print(f"  List with {len(data)} items")
                if data:
                    print(f"  First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else type(data[0])}")
            elif isinstance(data, dict):
                print(f"  Dict with keys: {list(data.keys())[:10]}")
            else:
                print(f"  Type: {type(data)}")
        except Exception as e:
            print(f"  Error: {e}")
    else:
        print("  NOT FOUND")

# Also check what the briefing code resolves to
web_dir = '/workspace/web'
resolved = os.path.normpath(os.path.join(web_dir, '..', 'brain', 'plans.json'))
print(f"\nResolved briefing path: {resolved}")
print(f"Exists: {os.path.exists(resolved)}")