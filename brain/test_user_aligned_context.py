"""
Test the user-aligned context module — verify it gathers real internal state
and produces rich, grounded system prompts for chat.
"""
import sys
sys.path.insert(0, '.')

from brain.user_aligned_context import (
    classify_query_intent,
    build_user_aligned_chat_context,
    get_emotional_state,
    get_active_plans_summary,
    get_recent_memories,
    compose_alive_system_prompt,
)


def test_intent_classification():
    """Verify query intent classification covers key categories."""
    cases = [
        ("How are you feeling?", "introspection"),
        ("What are your emotions like?", "emotional"),
        ("What are you working on?", "planning"),
        ("Do you remember yesterday?", "memory"),
        ("What is consciousness?", "philosophical"),
        ("Write me a poem", "creative"),
        ("How does your architecture work?", "technical"),
        ("Hello there", "general"),
        ("Tell me about yourself", "introspection"),
        ("What's your mood?", "emotional"),
        ("What are your plans?", "planning"),
    ]
    
    passed = 0
    for query, expected in cases:
        result = classify_query_intent(query)
        status = "✓" if result == expected else "✗"
        if result != expected:
            print(f"  {status} '{query}' → {result} (expected {expected})")
        else:
            passed += 1
    
    print(f"Intent classification: {passed}/{len(cases)} passed")
    return passed >= len(cases) - 2  # Allow 2 misclassifications


def test_context_building():
    """Verify the full context builder returns all expected fields."""
    ctx = build_user_aligned_chat_context("How are you feeling today?")
    
    required_fields = [
        'intent', 'emotional_state', 'active_plans', 'recent_memories',
        'reflections', 'lessons', 'alignment', 'system_prompt', 'query',
    ]
    
    missing = [f for f in required_fields if f not in ctx]
    if missing:
        print(f"  ✗ Missing fields: {missing}")
        return False
    
    # System prompt should be substantial
    prompt = ctx['system_prompt']
    if len(prompt) < 100:
        print(f"  ✗ System prompt too short: {len(prompt)} chars")
        return False
    
    # Should contain XTAgent identity
    if 'XTAgent' not in prompt:
        print(f"  ✗ System prompt doesn't mention XTAgent")
        return False
    
    # Should contain emotional data
    if 'Mood' not in prompt and 'Valence' not in prompt:
        print(f"  ✗ System prompt lacks emotional grounding")
        return False
    
    print(f"  ✓ Context built with {len(prompt)} char system prompt")
    print(f"    Intent: {ctx['intent']}")
    print(f"    Memories: {len(ctx['recent_memories'])}")
    print(f"    Plans: {len(ctx['active_plans'])}")
    print(f"    Lessons: {len(ctx['lessons'])}")
    return True


def test_system_prompt_adapts_to_intent():
    """Verify the system prompt changes based on query intent."""
    introspective = build_user_aligned_chat_context("How do you feel?")
    planning = build_user_aligned_chat_context("What are you working on?")
    philosophical = build_user_aligned_chat_context("What is consciousness?")
    
    p1 = introspective['system_prompt']
    p2 = planning['system_prompt']
    p3 = philosophical['system_prompt']
    
    # They should have different guidance sections
    checks = [
        ("introspection has inner experience guidance", "inner experience" in p1 or "ACTUAL emotional" in p1),
        ("planning has plans guidance", "ACTUAL plans" in p2),
        ("philosophical has unique perspective", "unique perspective" in p3 or "source code" in p3),
    ]
    
    passed = 0
    for desc, check in checks:
        status = "✓" if check else "✗"
        print(f"  {status} {desc}")
        if check:
            passed += 1
    
    return passed >= 2


def test_emotional_state_loading():
    """Verify emotional state can be loaded."""
    state = get_emotional_state()
    # Should return a dict, even if empty
    assert isinstance(state, dict), f"Expected dict, got {type(state)}"
    print(f"  ✓ Emotional state loaded: {list(state.keys())[:5]}")
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("Testing User-Aligned Chat Context")
    print("=" * 60)
    
    results = []
    for name, test_fn in [
        ("Intent Classification", test_intent_classification),
        ("Context Building", test_context_building),
        ("Prompt Adapts to Intent", test_system_prompt_adapts_to_intent),
        ("Emotional State Loading", test_emotional_state_loading),
    ]:
        print(f"\n{name}:")
        try:
            results.append(test_fn())
        except Exception as e:
            print(f"  ✗ Exception: {e}")
            results.append(False)
    
    print(f"\n{'=' * 60}")
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} passed")
    
    if passed == total:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")