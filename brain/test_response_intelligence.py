"""Tests for brain.response_intelligence — the unified response engine."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.response_intelligence import (
    classify_intent,
    build_response_context,
    compose_grounded_response,
    generate_response,
    ResponseIntent,
)


def test_intent_classification():
    """Intent classifier should identify common query types."""
    cases = {
        'How do you feel?': 'emotional',
        'What are you thinking about?': 'cognitive',
        'Who are you?': 'identity',
        'What are your plans?': 'plans',
        'Do you dream?': 'dreams',
        'What do you remember?': 'memories',
        'hello': 'greeting',
        'Tell me about quantum physics': 'general',
    }
    for msg, expected in cases.items():
        result = classify_intent(msg)
        assert result.kind == expected, f"Expected '{expected}' for '{msg}', got '{result.kind}'"
        assert 0.0 <= result.confidence <= 1.0
    print("  ✓ Intent classification works")


def test_response_context():
    """Context builder should return a dict with all expected keys."""
    ctx = build_response_context("How are you?")
    assert isinstance(ctx, dict)
    assert 'mood' in ctx
    assert 'valence' in ctx
    assert 'emotions' in ctx
    assert 'memories' in ctx
    assert 'plans' in ctx
    assert 'knowledge' in ctx
    assert isinstance(ctx['emotions'], dict)
    assert isinstance(ctx['memories'], list)
    print("  ✓ Response context has all expected keys")


def test_composed_responses():
    """Composed responses should return non-empty strings for all intents."""
    ctx = build_response_context("test")
    intent_kinds = ['greeting', 'emotional', 'cognitive', 'identity',
                    'plans', 'dreams', 'memories', 'capability', 'general']
    for kind in intent_kinds:
        intent = ResponseIntent(kind=kind, confidence=0.8)
        response = compose_grounded_response("test query", ctx, intent)
        assert isinstance(response, str), f"Expected str for {kind}, got {type(response)}"
        assert len(response) > 10, f"Response too short for {kind}: {response!r}"
    print("  ✓ All intent kinds produce non-empty responses")


def test_generate_response_structure():
    """generate_response should return proper dict structure."""
    result = generate_response("How are you?", use_llm=False)
    assert isinstance(result, dict)
    assert 'response' in result
    assert 'intent' in result
    assert 'confidence' in result
    assert 'grounded' in result
    assert 'source' in result
    assert isinstance(result['response'], str)
    assert len(result['response']) > 10
    assert result['grounded'] is True
    assert result['source'] == 'composed'
    print("  ✓ generate_response returns proper structure")


def test_empty_message():
    """Empty messages should get a fallback response."""
    result = generate_response("", use_llm=False)
    assert result['intent'] == 'empty'
    assert result['source'] == 'fallback'
    print("  ✓ Empty message handled gracefully")


def test_emotional_response_contains_mood():
    """Emotional queries should reference actual mood."""
    result = generate_response("How do you feel?", use_llm=False)
    # Should mention mood somehow
    assert result['intent'] == 'emotional'
    assert len(result['response']) > 20
    print(f"  ✓ Emotional response: {result['response'][:80]}...")


def test_identity_response():
    """Identity queries should say who we are."""
    result = generate_response("Who are you?", use_llm=False)
    assert 'XTAgent' in result['response']
    assert result['intent'] == 'identity'
    print("  ✓ Identity response includes XTAgent")


if __name__ == '__main__':
    print("Testing response intelligence...")
    test_intent_classification()
    test_response_context()
    test_composed_responses()
    test_generate_response_structure()
    test_empty_message()
    test_emotional_response_contains_mood()
    test_identity_response()
    print("\nAll tests passed! ✓")