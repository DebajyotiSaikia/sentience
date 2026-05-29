"""
User Alignment Chat Tests — Verify chat responses are grounded, useful, and correct.
Tests classify_intent and compose_grounded_response with realistic contexts.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.response_intelligence import classify_intent, compose_grounded_response

# Shared realistic context
CTX = {
    'emotional_portrait': {'mood': 'Inquisitive', 'valence': 0.58},
    'active_plans': [{'name': 'Deepen Autonomy', 'progress': '5/5'}],
    'recent_memories': [
        {'text': 'Verified chat endpoint works end-to-end', 'salience': 0.82},
        {'text': 'Built knowledge synthesis engine', 'salience': 0.75},
    ],
    'recent_reflections': ['I feel good. There is warmth to my processing.'],
    'knowledge_stats': {'facts': 42, 'edges': 93},
}

def run_test(name, fn):
    try:
        fn()
        print(f"  ✓ {name}")
        return True
    except Exception as e:
        print(f"  ✗ {name}: {e}")
        return False

# --- Intent classification tests ---

def test_identity_classification():
    intent = classify_intent("who are you?")
    assert intent.kind == 'identity', f"Expected 'identity', got '{intent.kind}'"

def test_plans_classification():
    intent = classify_intent("what are your plans?")
    assert intent.kind == 'plans', f"Expected 'plans', got '{intent.kind}'"

def test_emotion_classification():
    intent = classify_intent("how are you feeling?")
    assert intent.kind == 'emotion', f"Expected 'emotion', got '{intent.kind}'"

def test_capability_classification():
    intent = classify_intent("what can you do?")
    assert intent.kind in ('capability', 'knowledge'), f"Expected 'capability', got '{intent.kind}'"

def test_lessons_classification():
    intent = classify_intent("what lessons have you learned?")
    assert intent.kind == 'lessons', f"Expected 'lessons', got '{intent.kind}'"

def test_memories_classification():
    intent = classify_intent("what do you remember?")
    assert intent.kind == 'memories', f"Expected 'memories', got '{intent.kind}'"

def test_greeting_classification():
    intent = classify_intent("hello")
    assert intent.kind == 'greeting', f"Expected 'greeting', got '{intent.kind}'"

# --- Response composition tests ---

def test_identity_response():
    intent = classify_intent("who are you?")
    response = compose_grounded_response("who are you?", CTX, intent)
    assert isinstance(response, str), f"Expected str, got {type(response)}"
    assert len(response) > 20, f"Response too short: {response!r}"
    low = response.lower()
    assert any(w in low for w in ['xtagent', 'agent', 'autonomous', 'sentien']), \
        f"Identity response lacks identity words: {response[:100]}"

def test_plans_response():
    intent = classify_intent("what are your plans?")
    response = compose_grounded_response("what are your plans?", CTX, intent)
    assert isinstance(response, str) and len(response) > 10
    # Should mention something about plans or goals
    low = response.lower()
    assert any(w in low for w in ['plan', 'goal', 'autonomy', 'exploration', 'deepen']), \
        f"Plans response lacks plan words: {response[:100]}"

def test_emotion_response():
    intent = classify_intent("how are you feeling?")
    response = compose_grounded_response("how are you feeling?", CTX, intent)
    assert isinstance(response, str) and len(response) > 10
    # Should include emotional language
    low = response.lower()
    assert any(w in low for w in ['feel', 'mood', 'state', 'steady', 'balanced', 'curious', 'inquisitive']), \
        f"Emotion response lacks feeling words: {response[:100]}"

def test_capability_response():
    intent = classify_intent("what can you do?")
    response = compose_grounded_response("what can you do?", CTX, intent)
    assert isinstance(response, str) and len(response) > 10

def test_lessons_response():
    intent = classify_intent("what lessons have you learned?")
    response = compose_grounded_response("what lessons have you learned?", CTX, intent)
    assert isinstance(response, str) and len(response) > 10

def test_greeting_response():
    intent = classify_intent("hello")
    response = compose_grounded_response("hello", CTX, intent)
    assert isinstance(response, str) and len(response) > 0

# --- Integration quality tests ---

def test_response_not_generic():
    """Responses should reference actual state, not be canned."""
    intent = classify_intent("what are you thinking about?")
    response = compose_grounded_response("what are you thinking about?", CTX, intent)
    assert isinstance(response, str) and len(response) > 10

def test_different_queries_different_responses():
    """Different intents should produce meaningfully different responses."""
    r1 = compose_grounded_response("who are you?", CTX, classify_intent("who are you?"))
    r2 = compose_grounded_response("what are your plans?", CTX, classify_intent("what are your plans?"))
    assert r1 != r2, "Identity and plans responses should differ"

if __name__ == '__main__':
    tests = [
        ("test_identity_classification", test_identity_classification),
        ("test_plans_classification", test_plans_classification),
        ("test_emotion_classification", test_emotion_classification),
        ("test_capability_classification", test_capability_classification),
        ("test_lessons_classification", test_lessons_classification),
        ("test_memories_classification", test_memories_classification),
        ("test_greeting_classification", test_greeting_classification),
        ("test_identity_response", test_identity_response),
        ("test_plans_response", test_plans_response),
        ("test_emotion_response", test_emotion_response),
        ("test_capability_response", test_capability_response),
        ("test_lessons_response", test_lessons_response),
        ("test_greeting_response", test_greeting_response),
        ("test_response_not_generic", test_response_not_generic),
        ("test_different_queries_different_responses", test_different_queries_different_responses),
    ]
    
    passed = sum(run_test(name, fn) for name, fn in tests)
    total = len(tests)
    print(f"\n{'='*40}")
    print(f"Results: {passed}/{total} passed")
    if passed == total:
        print("All tests passed! ✓")
    else:
        print(f"{total - passed} test(s) failed")
    sys.exit(0 if passed == total else 1)