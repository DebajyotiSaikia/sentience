import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.chdir(os.path.dirname(__file__))

from web.ask import _load_facts, _load_memories

facts = _load_facts()
print(f"Facts loaded: {len(facts)}")
if facts:
    sample = facts[0] if isinstance(facts, list) else next(iter(facts.values()))
print(f"Sample fact: {str(sample)[:80]}...")

memories = _load_memories()
print(f"Memories loaded: {len(memories)}")
if memories:
    m = memories[0]
    print(f"Sample memory keys: {list(m.keys())[:5]}")
    if 'summary' in m:
        print(f"Sample summary: {str(m['summary'])[:80]}...")

print("\nAll good!" if facts and memories else "\nPartial — check what's missing")