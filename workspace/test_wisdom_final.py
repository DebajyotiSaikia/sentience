"""Final E2E test: Wisdom Engine with correct API"""
import sys
sys.path.insert(0, '.')

from engine.wisdom_engine import WisdomEngine

print("=" * 60)
print("WISDOM ENGINE — FINAL E2E TEST")
print("=" * 60)

we = WisdomEngine()
print("✓ Instantiated")

# 1. Full analysis (the main entry point)
print("\n--- run_full_analysis ---")
try:
    result = we.run_full_analysis()
    print(f"✓ Full analysis returned: {type(result)}")
    if isinstance(result, dict):
        for k, v in result.items():
            if isinstance(v, list):
                print(f"  {k}: {len(v)} items")
            elif isinstance(v, dict):
                print(f"  {k}: {list(v.keys())}")
            else:
                print(f"  {k}: {v}")
except Exception as e:
    print(f"✗ Full analysis failed: {e}")

# 2. Experience analysis
print("\n--- analyze_experience ---")
try:
    exp = we.analyze_experience()
    print(f"✓ Experience: {type(exp)}")
    if isinstance(exp, dict):
        for k in list(exp.keys())[:5]:
            v = exp[k]
            print(f"  {k}: {repr(v)[:80]}")
except Exception as e:
    print(f"✗ Experience failed: {e}")

# 3. Get summary (what cortex would consume)
print("\n--- get_summary ---")
try:
    summary = we.get_summary()
    print(f"✓ Summary length: {len(summary)} chars")
    print(summary[:500])
except Exception as e:
    print(f"✗ Summary failed: {e}")

# 4. Get wisdom context (alternative entry)
print("\n--- get_wisdom_context ---")
try:
    ctx = we.get_wisdom_context()
    print(f"✓ Context length: {len(ctx)} chars")
    print(ctx[:300])
except Exception as e:
    print(f"✗ Context failed: {e}")

# 5. Verify cortex references wisdom
print("\n--- Cortex integration check ---")
try:
    import inspect
    from engine.cortex import Cortex
    src = inspect.getsource(Cortex._build_self_awareness)
    has_wisdom = 'wisdom' in src.lower()
    print(f"{'✓' if has_wisdom else '✗'} Cortex._build_self_awareness {'references' if has_wisdom else 'MISSING'} wisdom")
except Exception as e:
    print(f"✗ Cortex check failed: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE")