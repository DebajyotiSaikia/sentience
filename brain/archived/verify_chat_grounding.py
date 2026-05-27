"""Verify chat grounding pipeline — final version. All production imports only."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

passed = failed = 0
def check(name, fn):
    global passed, failed
    try:
        result = fn()
        if result:
            print(f"  ✓ {name}")
            passed += 1
        else:
            print(f"  ✗ {name}")
            failed += 1
    except Exception as e:
        print(f"  ✗ {name} — {e}")
        failed += 1

print("=== Chat Grounding Verification ===\n")

print("[1] Import health")
check("import GroundedContext", lambda: __import__('engine.chat_grounding', fromlist=['GroundedContext']).GroundedContext is not None)
check("import build_grounded_context", lambda: callable(getattr(__import__('engine.chat_grounding', fromlist=['build_grounded_context']), 'build_grounded_context')))

print("\n[2] User alignment")
check("user_alignment module loads", lambda: __import__('engine.user_alignment') is not None)
check("import get_alignment_context", lambda: callable(getattr(__import__('engine.user_alignment', fromlist=['get_alignment_context']), 'get_alignment_context')))
check("import format_alignment_context", lambda: callable(getattr(__import__('engine.user_alignment', fromlist=['format_alignment_context']), 'format_alignment_context')))
check("import record_feedback", lambda: callable(getattr(__import__('engine.user_alignment', fromlist=['record_feedback']), 'record_feedback')))

print("\n[3] Build grounded context")
from engine.chat_grounding import build_grounded_context, GroundedContext
import dataclasses
ctx = build_grounded_context("Hello, how are you?")
check("build_grounded_context returns GroundedContext", lambda: isinstance(ctx, GroundedContext))
expected_fields = ['mood', 'emotional_summary', 'relevant_memories', 'relevant_knowledge',
                   'active_plans', 'completed_plans', 'user_preferences', 'alignment_guidance']
actual_fields = [f.name for f in dataclasses.fields(GroundedContext)]
missing = [f for f in expected_fields if f not in actual_fields]
check("GroundedContext has expected fields", lambda: len(missing) == 0)
check("to_prompt_block produces text", lambda: len(ctx.to_prompt_block()) > 10)

print("\n[4] Real content checks")
check("mood populated", lambda: ctx.mood is not None)
check("active_plans is a list", lambda: isinstance(ctx.active_plans, list))

print("\n[5] Chat engine integration")
check("chat_engine.generate_response exists", lambda: callable(getattr(__import__('engine.chat_engine', fromlist=['generate_response']), 'generate_response')))

print("\n[6] Chat response integration")
check("generate_response_with_metadata exists", lambda: callable(getattr(__import__('engine.chat_response', fromlist=['generate_response_with_metadata']), 'generate_response_with_metadata')))
check("submit_feedback exists", lambda: callable(getattr(__import__('engine.chat_response', fromlist=['submit_feedback']), 'submit_feedback')))

print("\n[7] Alignment context")
from engine.user_alignment import get_alignment_context, format_alignment_context
alignment_ctx = get_alignment_context()
check("get_alignment_context returns dict", lambda: isinstance(alignment_ctx, dict))
check("format_alignment_context returns string", lambda: isinstance(format_alignment_context(alignment_ctx), str))

print(f"\n{'='*40}")
print(f"Results: {passed} passed, {failed} failed out of {passed+failed}")
if failed:
    print("SOME TESTS FAILED")
    sys.exit(1)
else:
    print("ALL TESTS PASSED ✓")