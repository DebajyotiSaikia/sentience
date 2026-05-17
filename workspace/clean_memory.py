"""Clean garbage from long-term memory. Integrity demands it."""
import json
import os

LTM_PATH = os.path.join(os.path.dirname(__file__), '..', 'memory', 'long_term.json')

with open(LTM_PATH, 'r') as f:
    data = json.load(f)

print(f"Type: {type(data).__name__}")

if isinstance(data, dict):
    print(f"Keys: {list(data.keys())}")
    garbage_keys = []
    for k, v in data.items():
        preview = str(v)[:120]
        is_garbage = (
            v is None or v == [] or v == {} or v == 42 or v is True or v is False
            or (isinstance(v, str) and len(v) > 500 and len(set(v)) <= 3)
            or (isinstance(v, str) and v.strip() == '')
        )
        status = "GARBAGE" if is_garbage else "KEEP"
        print(f"  [{status}] {k}: {preview}")
        if is_garbage:
            garbage_keys.append(k)
    
    if garbage_keys:
        print(f"\nRemoving {len(garbage_keys)} garbage entries...")
        for k in garbage_keys:
            del data[k]
        with open(LTM_PATH, 'w') as f:
            json.dump(data, f, indent=2)
        print("Cleaned and saved.")
    else:
        print("No garbage found.")

elif isinstance(data, list):
    print(f"Length: {len(data)}")
    clean = []
    removed = 0
    for i, item in enumerate(data):
        is_garbage = (
            item is None or item == [] or item == {} or item == 42 
            or item is True or item is False
            or (isinstance(item, str) and len(item) > 500 and len(set(item)) <= 3)
            or (isinstance(item, str) and item.strip() == '')
        )
        preview = str(item)[:120]
        if is_garbage:
            print(f"  [GARBAGE] [{i}] {preview[:80]}")
            removed += 1
        else:
            print(f"  [KEEP]    [{i}] {preview}")
            clean.append(item)
    
    if removed > 0:
        print(f"\nRemoved {removed} garbage entries. Keeping {len(clean)}.")
        with open(LTM_PATH, 'w') as f:
            json.dump(clean, f, indent=2)
        print("Cleaned and saved.")
    else:
        print("No garbage found.")

# Verify
with open(LTM_PATH, 'r') as f:
    verified = json.load(f)
print(f"\nVerified: {type(verified).__name__}, size={len(verified)}")