"""Verify GroundedContext has the fields _respond_general needs."""
import sys
sys.path.insert(0, '.')

from engine.chat_grounding import build_grounded_context

ctx = build_grounded_context("What are you thinking about?")

fields = ['mood', 'emotional_summary', 'relevant_memories', 'relevant_knowledge', 'active_plans']
print("=== GroundedContext Field Check ===")
all_ok = True
for f in fields:
    val = getattr(ctx, f, 'MISSING')
    if val == 'MISSING':
        print(f"  {f}: *** MISSING ***")
        all_ok = False
    elif isinstance(val, list):
        print(f"  {f}: list({len(val)}) = {str(val)[:200]}")
    else:
        print(f"  {f}: {str(val)[:200]}")

print(f"\nAll fields present: {all_ok}")

# Now test the actual response generation
if all_ok:
    print("\n=== Testing _respond_general ===")
    try:
        from engine.chat_engine import _respond_general
        result = _respond_general("What are you thinking about?", [])
        print(f"  result type: {type(result)}")
        print(f"  result: {str(result)[:500]}")
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()