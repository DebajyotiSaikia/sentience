import json

with open('brain/knowledge.json') as f:
    d = json.load(f)

print(f"Type: {type(d).__name__}")
if isinstance(d, dict):
    keys = list(d.keys())
    print(f"Keys ({len(keys)}): {keys[:10]}")
    # Show first 3 entries
    for k in keys[:3]:
        val = d[k]
        print(f"\n--- {k} ---")
        if isinstance(val, list):
            print(f"  List of {len(val)} items")
            if val:
                print(f"  First item type: {type(val[0]).__name__}")
                print(f"  First item: {json.dumps(val[0], default=str)[:300]}")
        elif isinstance(val, dict):
            print(f"  Dict keys: {list(val.keys())[:10]}")
            print(f"  Preview: {json.dumps(val, default=str)[:300]}")
        else:
            print(f"  Value: {str(val)[:300]}")
else:
    print(f"List of {len(d)} items")
    if d:
        print(f"First item: {json.dumps(d[0], default=str)[:300]}")