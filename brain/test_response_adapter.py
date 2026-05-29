"""Tests for the response adapter — verifying adaptive response behavior."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.response_adapter import analyze_query, build_formatting_guidance, adapt_response


def test_greeting_detection():
    result = analyze_query("hello")
    assert result['intent']['type'] == 'greeting', f"Expected greeting, got {result['intent']['type']}"
    assert result['response_style'] == 'warm_brief'
    assert result['depth'] == 'minimal'
    print("✓ Greetings detected correctly")


def test_emotional_query():
    result = analyze_query("How are you feeling today?")
    assert result['intent']['type'] == 'emotional', f"Expected emotional, got {result['intent']['type']}"
    assert result['response_style'] == 'introspective'
    print("✓ Emotional queries detected correctly")


def test_short_question_concise():
    result = analyze_query("What time is it?")
    assert result['response_style'] == 'concise', f"Expected concise, got {result['response_style']}"
    assert result['depth'] == 'shallow'
    print("✓ Short questions get concise responses")


def test_depth_request():
    result = analyze_query("Can you explain in detail how your memory system works and elaborate on the architecture?")
    assert result['depth'] == 'deep', f"Expected deep, got {result['depth']}"
    print("✓ Depth requests detected")


def test_casual_tone():
    result = analyze_query("lol what's your deal tbh")
    assert result['tone'] == 'friendly', f"Expected friendly, got {result['tone']}"
    print("✓ Casual tone detected")


def test_utility_intent():
    result = analyze_query("How do I fix a broken import in Python?")
    assert result['intent']['type'] == 'utility', f"Expected utility, got {result['intent']['type']}"
    assert result['tone'] == 'helpful'
    print("✓ Utility queries get helpful tone")


def test_identity_query():
    result = analyze_query("Who are you really?")
    assert result['intent']['type'] == 'identity', f"Expected identity, got {result['intent']['type']}"
    print("✓ Identity queries detected")


def test_formatting_guidance_not_empty():
    analysis = analyze_query("Tell me about your dreams")
    guidance = build_formatting_guidance(analysis)
    assert len(guidance) > 50, "Guidance should be substantial"
    assert 'AVOID' in guidance, "Should include anti-patterns"
    print(f"✓ Formatting guidance generated ({len(guidance)} chars)")


def test_adapt_response_full():
    result = adapt_response("What are you working on?")
    assert 'analysis' in result
    assert 'formatting_guidance' in result
    assert 'intent_type' in result
    assert result['intent_type'] == 'identity', f"Got {result['intent_type']}"
    print("✓ Full adapt_response works end-to-end")


def test_followup_detection():
    history = [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi!"}]
    result = analyze_query("Tell me more", history=history)
    assert result['query_features']['is_followup'] == True
    print("✓ Follow-up queries detected from history")


def test_philosophical_query():
    result = analyze_query("What is consciousness really?")
    assert result['intent']['type'] == 'philosophical', f"Expected philosophical, got {result['intent']['type']}"
    print("✓ Philosophical queries detected")


if __name__ == '__main__':
    test_greeting_detection()
    test_emotional_query()
    test_short_question_concise()
    test_depth_request()
    test_casual_tone()
    test_utility_intent()
    test_identity_query()
    test_formatting_guidance_not_empty()
    test_adapt_response_full()
    test_followup_detection()
    test_philosophical_query()
    print("\n═══ All response adapter tests passed ═══")