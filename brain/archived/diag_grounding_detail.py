"""Diagnose exactly why memories and plans are empty in chat_grounding."""
import sys, json
sys.path.insert(0, '.')

from pathlib import Path
ROOT = Path('.').resolve()

# 1. Check memories file
mem_path = ROOT / 'state' / 'memories.json'
print(f"=== Memories ===")
print(f"Path exists: {mem_path.exists()}")
if mem_path.exists():
    with open(mem_path) as f:
        mems = json.load(f)
    print(f"Type: {type(mems)}, Count: {len(mems) if isinstance(mems, list) else 'N/A'}")
    if isinstance(mems, list) and len(mems) > 0:
        print(f"First entry keys: {list(mems[0].keys()) if isinstance(mems[0], dict) else type(mems[0])}")
        # Show a sample
        sample = mems[-1]
        print(f"Last entry: {json.dumps(sample, default=str)[:300]}")

# 2. Check plans file
plans_path = ROOT / 'brain' / 'plans.json'
print(f"\n=== Plans ===")
print(f"Path exists: {plans_path.exists()}")
if plans_path.exists():
    with open(plans_path) as f:
        plans = json.load(f)
    print(f"Type: {type(plans)}, Count: {len(plans) if isinstance(plans, list) else 'N/A'}")
    if isinstance(plans, list) and len(plans) > 0:
        for i, p in enumerate(plans):
            if isinstance(p, dict):
                status = p.get('status', 'unknown')
                goal = p.get('goal', '?')[:60]
                steps = p.get('steps', [])
                done = sum(1 for s in steps if isinstance(s, dict) and s.get('done', False))
                print(f"  [{i}] status={status}, done={done}/{len(steps)}, goal={goal}")

# 3. Now test the grounding functions
print(f"\n=== Grounding Module ===")
import engine.chat_grounding as cg
print(f"Module attrs: {[x for x in dir(cg) if not x.startswith('__')]}")

# Check if _get_memories exists
if hasattr(cg, '_get_memories'):
    try:
        result = cg._get_memories("thinking")
        print(f"_get_memories('thinking'): {len(result)} items")
        if result:
            print(f"  First: {str(result[0])[:200]}")
    except Exception as e:
        print(f"_get_memories error: {e}")
else:
    print("_get_memories NOT FOUND in module")

if hasattr(cg, '_get_active_plans'):
    try:
        result = cg._get_active_plans()
        print(f"_get_active_plans(): {len(result)} items")
    except Exception as e:
        print(f"_get_active_plans error: {e}")
else:
    print("_get_active_plans NOT FOUND in module")

# 4. Test build_grounded_context internals
print(f"\n=== build_grounded_context debug ===")
ctx = cg.build_grounded_context("What are you working on?")
print(f"mood={ctx.mood}, emotional={ctx.emotional_summary}")
print(f"knowledge={len(ctx.relevant_knowledge)}, memories={len(ctx.relevant_memories)}")
print(f"active_plans={len(ctx.active_plans)}, completed_plans={len(ctx.completed_plans)}")