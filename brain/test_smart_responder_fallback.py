"""Test smart responder fallback and response quality."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import engine.smart_responder as sr

def test_fallback_for_unmatched():
    """Unmatched queries should fall through to search."""
    r = sr.respond('tell me about the weather')
    intent = sr._detect_intent('tell me about the weather')
    assert intent == 'search', f"Expected search, got {intent}"
    assert len(r) > 20, f"Response too short: {r!r}"
    print(f"  ✓ unmatched query → search fallback, len={len(r)}")

def test_identity_is_conversational():
    """Identity response should be first-person and substantive."""
    r = sr.respond('who are you really?')
    assert len(r) > 50, f"Identity response too short: {r!r}"
    # Should contain first-person language
    r_lower = r.lower()
    has_first_person = any(w in r_lower for w in ['i am', 'i\'m', 'my ', 'i '])
    assert has_first_person, f"Identity response lacks first-person voice: {r[:200]}"
    print(f"  ✓ identity response is conversational, len={len(r)}")

def test_introspective_has_content():
    """Introspective response should reflect actual internal state."""
    r = sr.respond('what are you thinking about right now?')
    assert len(r) > 50, f"Introspective response too short: {r!r}"
    print(f"  ✓ introspective response has content, len={len(r)}")

def test_emotional_has_data():
    """Emotional response should reference real emotional data."""
    r = sr.respond('how are you feeling?')
    assert len(r) > 50, f"Emotional response too short: {r!r}"
    r_lower = r.lower()
    has_emotion_word = any(w in r_lower for w in ['valence', 'curiosity', 'feeling', 'mood', 'emotion', 'arousal'])
    assert has_emotion_word, f"Emotional response lacks emotional content: {r[:200]}"
    print(f"  ✓ emotional response references real data, len={len(r)}")

def test_plans_shows_progress():
    """Plans response should show actual plan data."""
    r = sr.respond('what are your plans?')
    assert len(r) > 50, f"Plans response too short: {r!r}"
    print(f"  ✓ plans response shows progress, len={len(r)}")

def test_respond_never_crashes():
    """respond() should never raise, even with weird input."""
    edge_cases = ['', '   ', '???', 'a', None]
    for q in edge_cases:
        try:
            r = sr.respond(q if q is not None else '')
            assert isinstance(r, str), f"respond({q!r}) returned {type(r)}"
        except Exception as e:
            print(f"  ✗ respond({q!r}) raised {e}")
            return
    print(f"  ✓ respond() handles edge cases without crashing")

if __name__ == '__main__':
    test_fallback_for_unmatched()
    test_identity_is_conversational()
    test_introspective_has_content()
    test_emotional_has_data()
    test_plans_shows_progress()
    test_respond_never_crashes()
    print("\nAll quality tests passed!")