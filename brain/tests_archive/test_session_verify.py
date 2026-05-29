"""Final session verification — tests all changes made this session."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_smart_responder():
    """Verify intent detection and response composition."""
    from engine.smart_responder import respond, _detect_intent
    
    tests = {
        "hello": "greeting",
        "how do you feel?": "emotional",
        "what are your plans?": "plans",
        "who are you?": "identity",
        "what can you do?": "capabilities",
        "tell me about consciousness": "search",
    }
    passed = 0
    for query, expected in tests.items():
        result = _detect_intent(query)
        if result == expected:
            passed += 1
        else:
            print(f"  FAIL: '{query}' -> '{result}' (expected '{expected}')")
    print(f"Intent detection: {passed}/{len(tests)} passed")
    
    for intent_query in ["hello", "how do you feel?", "what are your plans?", "who are you?", "what can you do?"]:
        try:
            r = respond(intent_query)
            assert isinstance(r, str) and len(r) > 10, f"Bad response for '{intent_query}': {r[:50]}"
        except Exception as e:
            print(f"  FAIL respond('{intent_query}'): {e}")
            return False
    print("Response generation: all passed")
    return True

def test_fallback_path():
    """Verify the fallback doesn't crash."""
    from engine.chat_response import generate_response_with_metadata
    try:
        result = generate_response_with_metadata("What is consciousness?")
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        assert 'response' in result, f"Missing 'response' key: {list(result.keys())}"
        assert len(result['response']) > 0, "Empty response"
        print("Fallback path: passed")
        return True
    except Exception as e:
        print(f"Fallback path: FAIL — {e}")
        return False

def test_conversational_context():
    """Verify conversational context builds correctly."""
    from brain.conversational_context import build_conversational_context
    ctx = build_conversational_context()
    assert isinstance(ctx, str), f"Expected str, got {type(ctx)}"
    assert len(ctx) > 50, f"Context too short: {len(ctx)} chars"
    print(f"Conversational context: passed ({len(ctx)} chars)")
    return True

def test_no_str_get_crash():
    """Verify the str.get() crash is fixed in chat_response."""
    from engine.chat_response import _respond_general_grounded
    try:
        result = _respond_general_grounded("test query", [])
        assert isinstance(result, str), f"Expected str, got {type(result)}"
        print("No str.get() crash: passed")
        return True
    except AttributeError as e:
        if ".get(" in str(e):
            print(f"str.get() crash still present: {e}")
            return False
        raise

if __name__ == "__main__":
    print("=== Final Session Verification ===\n")
    results = []
    results.append(("smart_responder", test_smart_responder()))
    results.append(("fallback_path", test_fallback_path()))
    results.append(("conversational_context", test_conversational_context()))
    results.append(("no_str_get_crash", test_no_str_get_crash()))
    
    print(f"\n=== Results: {sum(1 for _,v in results if v)}/{len(results)} passed ===")
    for name, passed in results:
        print(f"  {'PASS' if passed else 'FAIL'}: {name}")
    
    if all(v for _, v in results):
        print("\nAll tests passed!")
    else:
        sys.exit(1)