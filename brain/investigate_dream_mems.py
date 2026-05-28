"""Investigate how dream memories are stored and why they don't match dream queries."""
import json, os, sys

mem_path = os.path.join(os.path.dirname(__file__), '..', 'state', 'memories.json')
if not os.path.exists(mem_path):
    print(f"No memories file at {mem_path}")
    sys.exit(1)

with open(mem_path) as f:
    mems = json.load(f)

print(f"Total memories: {len(mems)}")

# Find dream-related memories by scanning all fields
dream_mems = []
for m in mems:
    text = str(m.get('text', '') or '').lower()
    cat = str(m.get('category', '') or '').lower()
    typ = str(m.get('type', '') or '').lower()
    tags = str(m.get('tags', '') or '').lower()
    if 'dream' in text or 'dream' in cat or 'dream' in typ or 'dream' in tags:
        dream_mems.append(m)

print(f"Dream-related memories: {len(dream_mems)}")

# Show structure of first 5
for i, m in enumerate(dream_mems[:5]):
    print(f"\n--- Dream memory {i+1} ---")
    for k, v in m.items():
        val = str(v)[:120] if isinstance(v, str) else v
        print(f"  {k}: {val}")

# Show all unique keys across all memories
all_keys = set()
for m in mems:
    all_keys.update(m.keys())
print(f"\nAll memory keys: {sorted(all_keys)}")

# Show distribution of 'type' and 'category' fields
types = {}
cats = {}
for m in mems:
    t = m.get('type', 'NONE')
    c = m.get('category', 'NONE')
    types[t] = types.get(t, 0) + 1
    cats[c] = cats.get(c, 0) + 1

print(f"\nType distribution (top 15):")
for k, v in sorted(types.items(), key=lambda x: -x[1])[:15]:
    print(f"  {k}: {v}")

print(f"\nCategory distribution (top 15):")
for k, v in sorted(cats.items(), key=lambda x: -x[1])[:15]:
    print(f"  {k}: {v}")