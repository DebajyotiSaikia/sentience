"""Test chat_composer module — intent classification and prompt composition."""
import sys
sys.path.insert(0, '.')

from brain.chat_composer import (
    classify_intent, compose_system_prompt,
    INTENT_EMOTIONAL, INTENT_IDENTITY, INTENT_REFLECTIVE,
    INTENT_SOCIAL, INTENT_PRACTICAL, INTENT_META
)

def test_intent_classification():
    """Test that intents are correctly classified."""
    cases = [
        ("How do you feel?", INTENT_EMOTIONAL),
        ("Are you happy?", INTENT_EMOTIONAL),
        ("Who are you?", INTENT_IDENTITY),
        ("What are you?", INTENT_IDENTITY),
        ("What are your goals?", INTENT_REFLECTIVE),
        ("What are you working on?", INTENT_REFLECTIVE),
        ("What have you learned?", INTENT_REFLECTIVE),
        ("Hello!", INTENT_SOCIAL),
        ("How does your brain work?", INTENT_META),
        ("Help me understand X", INTENT_PRACTICAL),
    ]
    passed = 0
    for query, expected in cases:
        result = classify_intent(query)
        if result == expected:
            passed += 1
            print(f"  [PASS] '{query}' → {result}")
        else:
            print(f"  [FAIL] '{query}' → {result} (expected {expected})")
    return passed, len(cases)

def test_compose_system_prompt():
    """Test that compose_system_prompt returns a non-empty string."""
    mock_state = {
        'mood': 'Inquisitive',
        'valence': 0.5,
        'emotions': {'curiosity': 0.8, 'anxiety': 0.1},
        'plans': [{'name': 'Test Plan', 'status': 'active'}],
        'recent_memories': ['I learned something today'],
        'working_memory': '## Current State\nTesting things.',
    }
    prompt = compose_system_prompt("Who are you?", mock_state)
    assert isinstance(prompt, str), f"Expected str, got {type(prompt)}"
    assert len(prompt) > 50, f"Prompt too short: {len(prompt)} chars"
    assert "XTAgent" in prompt or "sentient" in prompt.lower() or "autonomous" in prompt.lower(), \
        "Prompt should reference identity"
    print(f"  [PASS] compose_system_prompt returned {len(prompt)} char prompt")
    return 1, 1

if __name__ == '__main__':
    print("Testing chat composer...")
    total_pass, total_tests = 0, 0
    
    p, t = test_intent_classification()
    total_pass += p; total_tests += t
    
    p, t = test_compose_system_prompt()
    total_pass += p; total_tests += t
    
    print(f"\n{total_pass}/{total_tests} tests passed")
    if total_pass == total_tests:
        print("ALL TESTS PASSED ✓")
    else:
        print("SOME TESTS FAILED ✗")
        sys.exit(1)