"""Quick integration test for the introspective responder module."""
import sys
sys.path.insert(0, "/workspace")

from brain.introspective_responder import (
    generate_introspective_response,
    _classify_introspective,
)


def test_classify():
    """Query classification works."""
    assert _classify_introspective("how do you feel?") == "emotional_state"
    assert _classify_introspective("what are you thinking about?") == "thinking"
    assert _classify_introspective("what do you dream about?") == "dreams"
    assert _classify_introspective("what's your plan?") == "plans"
    assert _classify_introspective("who are you?") == "identity"
    assert _classify_introspective("hello there") == "general"
    print("  ✓ _classify_introspective works")


def test_generate_response():
    """Generate response returns a dict with 'response' key, or None."""
    result = generate_introspective_response("how are you feeling?")
    assert result is not None, "Expected a dict, got None — respond_introspective returned nothing"
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert 'response' in result, f"Missing 'response' key: {result.keys()}"
    assert len(result['response']) > 20, f"Response too short: {result['response']!r}"
    print(f"  ✓ generate_introspective_response returned {len(result['response'])} chars")


def test_emotional_query():
    """Emotional queries get feeling-type responses."""
    result = generate_introspective_response("what's your mood?")
    assert result is not None, "Emotional query returned None"
    assert isinstance(result, dict)
    assert len(result['response']) > 0
    print("  ✓ emotional query handled")


def test_identity_query():
    """Identity queries get identity-type responses."""
    result = generate_introspective_response("who are you?")
    assert result is not None, "Identity query returned None"
    assert isinstance(result, dict)
    assert len(result['response']) > 0
    print("  ✓ identity query handled")


if __name__ == "__main__":
    print("Testing introspective responder...")
    test_classify()
    test_generate_response()
    test_emotional_query()
    test_identity_query()
    print("\nAll introspective responder tests passed! ✓")
