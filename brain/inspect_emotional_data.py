"""Inspect emotional history data structure for timeline visualization."""
import json
import os
import glob

# Check state/emotional_history.json
hist_path = 'state/emotional_history.json'
if os.path.exists(hist_path):
    with open(hist_path) as f:
        data = json.load(f)
    print(f"=== {hist_path} ===")
    print(f"Type: {type(data).__name__}")
    if isinstance(data, list):
        print(f"Entries: {len(data)}")
        if data:
            print(f"First: {json.dumps(data[0], indent=2)[:400]}")
            print(f"Last: {json.dumps(data[-1], indent=2)[:400]}")
    elif isinstance(data, dict):
        print(f"Keys: {list(data.keys())[:10]}")
        for k in list(data.keys())[:2]:
            print(f"  {k}: {json.dumps(data[k], indent=2)[:300]}")
else:
    print(f"{hist_path} not found")

# Check state/emotional_state.json
state_path = 'state/emotional_state.json'
if os.path.exists(state_path):
    with open(state_path) as f:
        state = json.load(f)
    print(f"\n=== {state_path} ===")
    print(json.dumps(state, indent=2)[:500])

# Check for any other emotional data
print("\n=== Other emotional data files ===")
for pattern in ['state/emotion*', 'persist/emotion*', 'data/emotion*']:
    for f in glob.glob(pattern):
        size = os.path.getsize(f)
        print(f"  {f} ({size} bytes)")

# Check persist/memories.json for emotional data in memories
mem_path = 'persist/memories.json'
if os.path.exists(mem_path):
    with open(mem_path) as f:
        mems = json.load(f)
    print(f"\n=== {mem_path} ===")
    print(f"Total memories: {len(mems)}")
    if mems and isinstance(mems, list):
        sample = mems[-1]
        print(f"Latest memory keys: {list(sample.keys()) if isinstance(sample, dict) else 'not a dict'}")
        print(f"Latest: {json.dumps(sample, indent=2)[:400]}")