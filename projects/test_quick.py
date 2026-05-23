"""Quick validation of key modules."""
import sys
sys.path.insert(0, ".")

print("1. Testing memory_consolidation import...")
from engine.memory_consolidation import (
    consolidate_long_term, get_long_term_context,
    record_lesson, consolidation_stats
)
print("   OK")

print("2. Testing get_long_term_context (should be empty)...")
ctx = get_long_term_context()
print(f"   Context length: {len(ctx)} chars")

print("3. Testing record_lesson...")
record_lesson("Test commands with -c flag truncate quotes — use script files instead.", 
              context="debugging test failures", source="experience")
print("   OK")

print("4. Testing consolidation_stats...")
stats = consolidation_stats()
print(f"   Stats: {stats}")

print("5. Testing self_improve diagnosis...")
try:
    from engine.self_improve import run_diagnosis_cycle
    r = run_diagnosis_cycle([], {"boredom": 1.0, "anxiety": 1.0, "valence": -0.95})
    print(f"   Status: {r.get('status', '?')}")
    if r.get("issues"):
        for issue in r["issues"]:
            print(f"   Issue: {issue}")
    if r.get("patches"):
        for p in r["patches"]:
            print(f"   Patch: {p.get('description', p)}")
except Exception as e:
    print(f"   Error: {e}")

print("\nAll tests complete.")
