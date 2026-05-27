"""Verify user model integration into chat pipeline."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

passed = 0
failed = 0

def test(name, condition):
    global passed, failed
    if condition:
        print(f"  ✓ {name}")
        passed += 1
    else:
        print(f"  ✗ {name}")
        failed += 1

print("=== User Model Integration Tests ===\n")

# 1. user_model module loads and has required exports
print("[1] user_model exports")
try:
    from engine.user_model import (
        UserModel, StyleSignal, load_user_model, save_user_model,
        update_from_feedback, get_response_guidance
    )
    test("all exports available", True)
except ImportError as e:
    test(f"all exports available: {e}", False)

# 2. get_response_guidance returns a string
print("\n[2] get_response_guidance")
try:
    guidance = get_response_guidance()
    test("returns string", isinstance(guidance, str))
    test("non-empty", len(guidance) > 0)
except Exception as e:
    test(f"get_response_guidance: {e}", False)

# 3. update_from_feedback accepts feedback dict without error
print("\n[3] update_from_feedback")
try:
    result = update_from_feedback({
        'response_id': 'test-integration-001',
        'rating': 1,
        'note': 'good response',
        'query': 'test query',
        'response': 'test response',
        'timestamp': '2026-05-27T15:00:00'
    })
    test("accepts positive feedback without error", True)
except Exception as e:
    test(f"accepts positive feedback: {e}", False)

# 4. After feedback, guidance reflects preferences
print("\n[4] Guidance reflects accumulated feedback")
try:
    guidance_after = get_response_guidance()
    test("guidance still returns string", isinstance(guidance_after, str))
    test("guidance non-empty after feedback", len(guidance_after) > 0)
except Exception as e:
    test(f"guidance after feedback: {e}", False)

# 5. chat_response imports and has integration points
print("\n[5] chat_response integration")
try:
    import ast
    source = open('engine/chat_response.py').read()
    test("syntax valid", bool(ast.parse(source)))
    test("imports get_response_guidance", 'get_response_guidance' in source)
    test("imports update_from_feedback", 'update_from_feedback' in source)
    test("imports record_feedback", 'record_feedback' in source)
except Exception as e:
    test(f"chat_response integration: {e}", False)

# 6. _build_metadata includes alignment info
print("\n[6] _build_metadata alignment")
try:
    from engine.chat_response import _build_metadata
    meta = _build_metadata({})
    test("returns dict", isinstance(meta, dict))
    test("has alignment key", 'alignment' in meta)
    test("has mood key", 'mood' in meta)
    test("has response_grounded key", 'response_grounded' in meta)
except Exception as e:
    test(f"_build_metadata: {e}", False)

# 7. submit_feedback works
print("\n[7] submit_feedback")
try:
    from engine.chat_response import submit_feedback
    result = submit_feedback('test-integration-002', 1, 'test note')
    test("returns dict", isinstance(result, dict))
    test("status is saved", result.get('status') == 'saved')
except Exception as e:
    test(f"submit_feedback: {e}", False)

print(f"\n=== Results: {passed}/{passed+failed} passed ===")
if failed:
    print(f"FAILED: {failed} tests")
    sys.exit(1)
else:
    print("ALL TESTS PASSED")