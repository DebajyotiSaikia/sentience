#!/usr/bin/env python3
"""Quick check of available state data shapes."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def show(label, path):
    if not os.path.exists(path):
        print(f"{label}: NOT FOUND")
        return None
    d = json.load(open(path))
    t = type(d).__name__
    if isinstance(d, list):
        print(f"{label}: list, len={len(d)}")
        if d and isinstance(d[0], dict):
            print(f"  keys: {list(d[0].keys())}")
            print(f"  sample: {str(d[0])[:120]}")
        elif d:
            print(f"  sample: {str(d[0])[:120]}")
    elif isinstance(d, dict):
        print(f"{label}: dict, keys={list(d.keys())[:10]}")
        for k, v in list(d.items())[:5]:
            print(f"  {k}: {str(v)[:100]}")
    return d

print("=== STATE DATA ===")
show("emotions", "state/emotions.json")
print()
show("plans", "state/plans.json")
print()
show("memories", "state/memories.json")
print()
show("identity", "state/identity.json")
print()
show("goals", "state/goals.json")
print()
show("survival", "state/survival_goals.json")
print()
show("lessons", "persist/long_term/lessons_learned.json")
print()
show("limbic", "state/limbic_state.json")
print()
show("status", "state/status.json")
print()

# Check working memory
wm_path = "state/working_memory.md"
if os.path.exists(wm_path):
    txt = open(wm_path).read()
    print(f"working_memory.md: {len(txt)} chars")
    print(f"  first 200: {txt[:200]}")
else:
    print("working_memory.md: NOT FOUND")
    # Check brain/ for it
    for p in ["brain/working_memory.md", "persist/working_memory.md"]:
        if os.path.exists(p):
            print(f"  Found at {p}")

print()
# Check what conversational_context produces
try:
    from brain.conversational_context import get_emotional_portrait, get_active_plans, get_recent_memories
    print("=== CONVERSATIONAL CONTEXT ===")
    ep = get_emotional_portrait()
    print(f"emotional_portrait: {str(ep)[:200]}")
    print()
    ap = get_active_plans()
    print(f"active_plans: {str(ap)[:200]}")
    print()
    rm = get_recent_memories()
    print(f"recent_memories: {str(rm)[:200]}")
except Exception as e:
    print(f"Error loading conversational_context: {e}")