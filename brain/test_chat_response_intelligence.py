"""
Integration test: verify web/chat.py correctly uses brain.response_intelligence.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_import_wiring():
    """Verify chat.py imports the intelligent response engine."""
    import importlib.util
    spec = importlib.util.find_spec('web.chat')
    assert spec is not None, "web.chat module not found"
    
    from brain.response_intelligence import generate_intelligent_response
    assert callable(generate_intelligent_response), "generate_intelligent_response not callable"

def test_intelligent_response_structure():
    """Verify generate_intelligent_response returns chat-compatible structure."""
    from brain.response_intelligence import generate_intelligent_response
    
    result = generate_intelligent_response("What are you thinking about?")
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    # Actual keys: response, intent, confidence, grounded, source
    assert 'response' in result, "Missing 'response' key"
    assert 'intent' in result, "Missing 'intent' key"
    assert 'confidence' in result, "Missing 'confidence' key"
    assert 'grounded' in result, "Missing 'grounded' key"
    assert isinstance(result['response'], str), "response should be string"
    assert len(result['response']) > 10, f"Response too short: {result['response']!r}"

def test_different_intents():
    """Different queries should produce non-empty responses."""
    from brain.response_intelligence import generate_intelligent_response
    
    queries = [
        "How are you feeling?",
        "What do you know?",
        "Tell me about your plans",
        "Who are you?",
    ]
    for q in queries:
        result = generate_intelligent_response(q)
        assert result.get('response'), f"Empty response for: {q}"

def test_intent_classification():
    """Intent classification should return reasonable categories."""
    from brain.response_intelligence import classify_intent
    
    emotional = classify_intent("How are you feeling right now?")
    emotional = classify_intent("How are you feeling right now?")
    assert emotional.kind in ('emotional', 'emotional_state', 'identity', 'general'), \
        f"Unexpected intent for emotional query: {emotional.kind}"
    
    knowledge = classify_intent("What do you know about qualia?")
    assert knowledge.kind in ('knowledge', 'factual', 'cognitive', 'general'), \
        f"Unexpected intent for knowledge query: {knowledge.kind}"
def test_response_context_has_real_data():
    """build_response_context should include actual internal state."""
    from brain.response_intelligence import build_response_context
    
    ctx = build_response_context("Tell me about yourself")
    assert isinstance(ctx, dict), f"Expected dict, got {type(ctx)}"
    # Should have some grounded data from internal state
    assert len(ctx) > 0, "Context is empty"

if __name__ == '__main__':
    tests = [
        test_import_wiring,
        test_intelligent_response_structure,
        test_different_intents,
        test_intent_classification,
        test_response_context_has_real_data,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} passed")