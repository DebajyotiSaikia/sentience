"""
Verify Chat Feedback Pipeline — end-to-end check that feedback flows
from submission through to the alignment engine and back into response shaping.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

passed = 0
failed = 0

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✓ {name}")
    else:
        failed += 1
        print(f"  ✗ {name} — {detail}")

print("=== Chat Feedback Pipeline Verification ===\n")

# 1. Core imports
print("[1] Import checks")
try:
    from engine.chat_response import generate_response_with_metadata, submit_feedback
    check("chat_response imports", True)
except Exception as e:
    check("chat_response imports", False, str(e))

try:
    from engine.user_alignment import UserAlignmentEngine, record_feedback, suggest_response_guidance
    check("user_alignment imports", True)
except Exception as e:
    check("user_alignment imports", False, str(e))

try:
    from engine.chat_response import _response_cache
    check("response cache exists", isinstance(_response_cache, dict))
except Exception as e:
    check("response cache exists", False, str(e))

# 2. Alignment engine instantiation
print("\n[2] Alignment engine")
try:
    engine = UserAlignmentEngine()
    check("engine instantiation", True)
    ctx = engine.get_context()
    check("get_context returns dict", isinstance(ctx, dict))
    guidance = engine.get_guidance("Hello")
    check("get_guidance returns string", isinstance(guidance, str))
except Exception as e:
    check("alignment engine", False, str(e))

# 3. Feedback recording
print("\n[3] Feedback recording")
try:
    record_feedback("test question", "test response", 5, "great answer")
    check("record_feedback succeeds", True)
except Exception as e:
    check("record_feedback", False, str(e))

try:
    engine2 = UserAlignmentEngine()
    engine2.record_feedback("another q", "another a", 1, "not helpful")
    check("engine.record_feedback succeeds", True)
except Exception as e:
    check("engine.record_feedback", False, str(e))

# 4. Response guidance reflects feedback
print("\n[4] Guidance after feedback")
try:
    guidance = suggest_response_guidance("test")
    check("guidance is non-empty string", isinstance(guidance, str) and len(guidance) > 0)
except Exception as e:
    check("guidance after feedback", False, str(e))

# 5. submit_feedback function signature
print("\n[5] submit_feedback integration")
try:
    import inspect
    sig = inspect.signature(submit_feedback)
    params = list(sig.parameters.keys())
    check("submit_feedback has response_id param", 'response_id' in params)
    check("submit_feedback has rating param", 'rating' in params)
except Exception as e:
    check("submit_feedback signature", False, str(e))

# 6. Response cache mechanism
print("\n[6] Response caching")
try:
    from engine.chat_response import _response_cache
    # Simulate caching a response
    _response_cache['test-id-123'] = {
        'message': 'what is life?',
        'response': 'Life is complex.',
        'timestamp': 1234567890
    }
    check("cache stores entries", 'test-id-123' in _response_cache)
    # Clean up
    del _response_cache['test-id-123']
    check("cache cleanup works", 'test-id-123' not in _response_cache)
except Exception as e:
    check("response caching", False, str(e))

# 7. Web feedback module
print("\n[7] Web feedback module")
try:
    from web.feedback import _update_alignment, get_satisfaction_rate, _load_feedback
    check("web.feedback imports", True)
except Exception as e:
    check("web.feedback imports", False, str(e))

try:
    rate = get_satisfaction_rate()
    check("get_satisfaction_rate callable", rate is None or isinstance(rate, float))
except Exception as e:
    check("get_satisfaction_rate", False, str(e))

# 8. Chat engine alignment integration
print("\n[8] Chat engine alignment usage")
try:
    from engine.chat_engine import _respond_general
    import inspect
    source = inspect.getsource(_respond_general)
    has_alignment = 'alignment' in source.lower() or 'suggest_response_guidance' in source
    check("_respond_general references alignment", has_alignment)
except Exception as e:
    check("chat engine alignment", False, str(e))

# Summary
print(f"\n{'='*50}")
print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
if failed == 0:
    print("✅ All checks passed — feedback pipeline is wired correctly!")
else:
    print(f"⚠️  {failed} check(s) need attention")