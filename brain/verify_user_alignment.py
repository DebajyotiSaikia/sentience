#!/usr/bin/env python3
"""Verify user alignment engine works end-to-end."""
import sys, os
sys.path.insert(0, '/workspace')

passed = 0
failed = 0

def check(name, condition):
    global passed, failed
    if condition:
        print(f"  ✓ {name}")
        passed += 1
    else:
        print(f"  ✗ {name}")
        failed += 1

print("=== User Alignment Engine Verification ===\n")

# 1. Import
print("[1] Import UserAlignmentEngine")
try:
    from engine.user_alignment import (
        UserAlignmentEngine, load_profile, record_feedback,
        get_alignment_context, suggest_response_guidance
    )
    check("Import succeeds", True)
except Exception as e:
    check(f"Import succeeds — {e}", False)
    sys.exit(1)

# 2. Instantiation
print("\n[2] Engine instantiation")
engine = UserAlignmentEngine()
check("Engine instantiates", engine is not None)
check("Profile has preferences", 'preferences' in engine._profile)
feedback_list = engine._profile.get('feedback', [])
check("Profile has feedback list", isinstance(feedback_list, list))

# 3. Record feedback via engine
print("\n[3] Record feedback via engine")
initial_count = len(engine._profile.get('feedback', []))
result = engine.record_feedback(
    "What are you thinking about?",
    "I'm currently focused on improving my chat responses.",
    rating=0.9,
    comment="Great answer"
)
check("record_feedback returns dict", isinstance(result, dict))
check("Result has status", result.get('status') == 'recorded')

# Reload profile to check persistence
engine._profile = load_profile()
new_count = len(engine._profile.get('feedback', []))
check("Feedback count incremented", new_count == initial_count + 1)

# 4. Module-level functions
print("\n[4] Module-level functions")
ctx = get_alignment_context()
check("get_alignment_context returns dict", isinstance(ctx, dict))
check("Context has preferences", 'preferences' in ctx)

guidance = suggest_response_guidance("Tell me about your plans")
check("suggest_response_guidance returns string", isinstance(guidance, str))
check("Guidance is non-empty", len(guidance) > 0)

# 5. Negative feedback learning
print("\n[5] Negative feedback")
result2 = engine.record_feedback(
    "What is 2+2?",
    "Well, that's an interesting philosophical question...",
    rating=0.2,
    comment="Just answer the question"
)
check("Negative feedback recorded", result2.get('status') == 'recorded')

# 6. Get guidance includes alignment info
print("\n[6] Integration check")
guidance2 = engine.get_guidance("How are you feeling?")
check("get_guidance returns string", isinstance(guidance2, str))

ctx2 = engine.get_context()
check("get_context returns dict", isinstance(ctx2, dict))

print(f"\n=== Results: {passed} passed, {failed} failed ===")
sys.exit(0 if failed == 0 else 1)