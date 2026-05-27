"""Test that chat_engine data loading works with state/ path."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path

# First check raw file access
DATA = Path('state')
files = ['knowledge_graph.json', 'plans.json', 'memories.json', 'emotional_state.json']
print("=== Raw file check ===")
for f in files:
    p = DATA / f
    print(f"  {f}: exists={p.exists()}", end="")
    if p.exists():
        import json
        with open(p) as fh:
            d = json.load(fh)
        if isinstance(d, dict):
            print(f", keys={list(d.keys())[:5]}, type=dict")
        elif isinstance(d, list):
            print(f", len={len(d)}, type=list")
        else:
            print(f", type={type(d).__name__}")
    else:
        print()

# Now test the actual functions
print("\n=== chat_engine functions ===")
from engine.chat_engine import _get_knowledge, _get_plans, _get_memories, _get_emotions

k = _get_knowledge()
print(f"  knowledge: count={k.get('count',0)}, nodes_type={type(k.get('nodes')).__name__}, edges={len(k.get('edges',[]))}")
if k.get('count', 0) == 0 and k.get('nodes'):
    print(f"    BUT nodes has {len(k['nodes'])} items! Count is wrong.")

p = _get_plans()
print(f"  plans: {len(p)} plans")
if p:
    print(f"    first: {p[0].get('name', 'unnamed')}")

m = _get_memories()
print(f"  memories: {len(m)} memories")
if m:
    print(f"    latest: {m[-1].get('content', m[-1].get('text', '?'))[:60]}")

e = _get_emotions()
print(f"  emotions: {list(e.keys())[:6]}")
print(f"    values: { {k: round(v,2) if isinstance(v, float) else v for k,v in list(e.items())[:5]} }")