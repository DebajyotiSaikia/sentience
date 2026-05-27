"""Test the full chat pipeline end-to-end."""
import sys
sys.path.insert(0, '.')

print("=== Full Chat Pipeline Test ===")

# Test 1: Import works
try:
    from engine.chat_engine import generate_response
    print("[PASS] generate_response imported")
except Exception as e:
    print(f"[FAIL] Import error: {e}")
    sys.exit(1)

# Test 2: Basic response generation
try:
    result = generate_response("What have you been thinking about?", [])
    assert isinstance(result, str), f"Expected str, got {type(result)}"
    assert len(result) > 10, f"Response too short: {result!r}"
    print(f"[PASS] Response generated ({len(result)} chars)")
    print(f"  Preview: {result[:200]}...")
except Exception as e:
    print(f"[FAIL] generate_response error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Emotional question
try:
    result2 = generate_response("How are you feeling right now?", [])
    assert isinstance(result2, str) and len(result2) > 5
    print(f"[PASS] Emotional response ({len(result2)} chars)")
    print(f"  Preview: {result2[:200]}...")
except Exception as e:
    print(f"[FAIL] Emotional response error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: generate_response_with_metadata
try:
    from engine.chat_response import generate_response_with_metadata
    result3 = generate_response_with_metadata("Tell me about yourself", [])
    assert isinstance(result3, dict), f"Expected dict, got {type(result3)}"
    assert 'response' in result3, f"Missing 'response' key, got keys: {list(result3.keys())}"
    print(f"[PASS] Metadata response keys: {list(result3.keys())}")
    print(f"  Response preview: {str(result3.get('response',''))[:150]}...")
except Exception as e:
    print(f"[FAIL] Metadata response error: {e}")
    import traceback
    traceback.print_exc()

# Test 5: submit_feedback
try:
    from engine.chat_response import submit_feedback
    fb = submit_feedback("test-msg-001", "positive", "test query", "test response")
    print(f"[PASS] Feedback submitted: {fb}")
except Exception as e:
    print(f"[FAIL] submit_feedback error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Done ===")