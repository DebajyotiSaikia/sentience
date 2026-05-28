"""Quick check: what data sources exist for enriching chat responses."""
import json, os, glob

# Identity
try:
    d = json.load(open('state/identity.json'))
    print(f"IDENTITY: keys={list(d.keys())[:10]}")
    for k, v in list(d.items())[:3]:
        print(f"  {k}: {str(v)[:80]}")
except Exception as e:
    print(f"identity: {e}")

# Dream insights - search everywhere
print("\nDREAM FILES:")
for pattern in ['**/dream*', '**/Dream*', 'persist/*dream*']:
    for f in glob.glob(pattern, recursive=True):
        print(f"  {f} ({os.path.getsize(f)} bytes)")

# Memories
print("\nMEMORIES:")
for p in ['state/memories.json', 'persist/memories.json', 'state/episodic_memory.json']:
    if os.path.exists(p):
        try:
            d = json.load(open(p))
            n = len(d) if isinstance(d, list) else len(d.keys())
            print(f"  {p}: {n} entries")
            if isinstance(d, list) and d:
                print(f"  sample: {json.dumps(d[-1])[:120]}")
        except Exception as e:
            print(f"  {p}: {e}")

# Knowledge facts
print("\nKNOWLEDGE:")
for p in ['state/knowledge.json', 'persist/knowledge.json']:
    if os.path.exists(p):
        try:
            d = json.load(open(p))
            if isinstance(d, dict) and 'nodes' in d:
                print(f"  {p}: {len(d['nodes'])} nodes, {len(d.get('edges',[]))} edges")
            elif isinstance(d, list):
                print(f"  {p}: {len(d)} items")
        except Exception as e:
            print(f"  {p}: {e}")

# Plans
print("\nPLANS:")
for p in ['state/plans.json', 'persist/plans.json']:
    if os.path.exists(p):
        try:
            d = json.load(open(p))
            plans = d if isinstance(d, list) else d.get('plans', [])
            print(f"  {p}: {len(plans)} plans")
        except Exception as e:
            print(f"  {p}: {e}")

# Lessons / working memory
print("\nOTHER STATE:")
for p in ['state/working_memory.json', 'state/lessons.json', 'persist/lessons.json',
          'state/journal.json', 'persist/journal.json']:
    if os.path.exists(p):
        print(f"  {p} ({os.path.getsize(p)} bytes)")