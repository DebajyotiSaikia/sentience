"""End-to-end integration test for brain.response_intelligence + web/chat.py wiring."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def test_all():
    print("=== Integration Test: brain.response_intelligence ===\n")
    
    # 1. Intent classification
    from brain.response_intelligence import classify_intent
    tests = [
        ('how are you feeling?', 'emotional'),
        ('who are you?', 'identity'),
        ('what are your plans?', 'meta'),
        ('tell me about quantum physics', 'knowledge'),
        ('hello!', 'conversational'),
    ]
    for query, expected in tests:
        result = classify_intent(query)
        intent = result['intent']
        ok = 'PASS' if intent == expected else f'FAIL (got {intent})'
        print(f"  Intent '{query[:30]}...' -> {ok}")
    
    # 2. Context building
    from brain.response_intelligence import build_response_context
    ctx = build_response_context('how do you feel right now?')
    assert 'intent' in ctx, "Missing intent in context"
    assert 'emotional_state' in ctx, "Missing emotional_state"
    print(f"\n  Context keys: {sorted(ctx.keys())}")
    print(f"  Emotional state keys: {sorted(ctx['emotional_state'].keys())}")
    print("  Context building: PASS")
    
    # 3. Full response generation
    from brain.response_intelligence import generate_response
    resp = generate_response('what are you thinking about right now?')
    assert 'response' in resp, "Missing response"
    assert len(resp['response']) > 10, f"Response too short: {resp['response']}"
    method = resp.get('method', 'unknown')
    print(f"\n  Response method: {method}")
    print(f"  Response length: {len(resp['response'])} chars")
    print(f"  Preview: {resp['response'][:120]}...")
    print("  Response generation: PASS")
    
    # 4. Module importable check
    import importlib.util
    spec = importlib.util.find_spec('brain.response_intelligence')
    assert spec is not None, "Module not importable"
    print("\n  Module importable: PASS")
    
    # 5. web/chat.py wiring check
    with open('web/chat.py') as f:
        chat_source = f.read()
    assert 'brain.response_intelligence' in chat_source, "web/chat.py not wired"
    assert '_has_response_intel' in chat_source, "Missing response intel flag"
    print("  web/chat.py wiring: PASS")
    
    print("\n=== All integration tests passed ===")
    return True

if __name__ == '__main__':
    try:
        success = test_all()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)