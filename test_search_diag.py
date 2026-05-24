from engine.knowledge_search import search_knowledge, search_facts, search_episodes, get_knowledge_stats

# What does the system think it has?
stats = get_knowledge_stats()
print("=== Knowledge Stats ===")
for k, v in stats.items():
    print(f"  {k}: {v}")

# Try searching with each function
print("\n=== search_knowledge('dream') ===")
r1 = search_knowledge("dream")
print(f"  Results: {len(r1) if hasattr(r1, '__len__') else r1}")
if r1 and hasattr(r1, '__len__') and len(r1) > 0:
    print(f"  First: {r1[0]}")

print("\n=== search_facts('dream') ===")
r2 = search_facts("dream")
print(f"  Results: {len(r2) if hasattr(r2, '__len__') else r2}")
if r2 and hasattr(r2, '__len__') and len(r2) > 0:
    print(f"  First: {r2[0]}")

print("\n=== search_episodes('dream') ===")
r3 = search_episodes("dream")
print(f"  Results: {len(r3) if hasattr(r3, '__len__') else r3}")
if r3 and hasattr(r3, '__len__') and len(r3) > 0:
    print(f"  First: {r3[0]}")

# Check what data files actually exist
import os, json
print("\n=== Data Files ===")
for root, dirs, files in os.walk("persist"):
    for f in sorted(files):
        path = os.path.join(root, f)
        size = os.path.getsize(path)
        print(f"  {path} ({size} bytes)")
        if f.endswith('.json') and size < 500000:
            try:
                with open(path) as fh:
                    data = json.load(fh)
                if isinstance(data, dict):
                    print(f"    dict with {len(data)} keys, sample: {list(data.keys())[:3]}")
                elif isinstance(data, list):
                    print(f"    list with {len(data)} items")
            except:
                pass

# Also check brain dir
for root, dirs, files in os.walk("brain"):
    for f in sorted(files):
        path = os.path.join(root, f)
        size = os.path.getsize(path)
        if 'knowledge' in f.lower() or 'fact' in f.lower() or 'graph' in f.lower():
            print(f"  {path} ({size} bytes)")