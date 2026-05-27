"""Verify user alignment pipeline end-to-end."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.user_alignment import (
    record_feedback, load_profile,
    get_alignment_guidance, summarize_alignment_state
)

passed = failed = 0

def check(name, cond):
    global passed, failed
    if cond:
        print(f"  [PASS] {name}"); passed += 1
    else:
        print(f"  [FAIL] {name}"); failed += 1

print("=" * 50)
print("USER ALIGNMENT PIPELINE VERIFICATION")
print("=" * 50)

print("\n1. Feedback persistence")
result = record_feedback(response_id="test-verify-001", rating=5, comment="Helpful")
check("record_feedback returns dict", isinstance(result, dict))

print("\n2. Profile loading")
profile = load_profile()
check("load_profile returns object", profile is not None)

print("\n3. Alignment guidance")
guidance = get_alignment_guidance()
check("returns string", isinstance(guidance, str))
check("non-empty", len(guidance) > 0)

print("\n4. Alignment state summary")
summary = summarize_alignment_state()
check("returns dict", isinstance(summary, dict))

print(f"\n{'=' * 50}")
print(f"Results: {passed} passed, {failed} failed")
if failed == 0:
    print("ALL TESTS PASSED")
else:
    sys.exit(1)