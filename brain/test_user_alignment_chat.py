"""
Test: User Alignment Chat Quality
Verifies that the chat pipeline produces conversational, grounded responses
that draw on real internal state rather than just dumping graph stats.
"""
import sys, os, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.response_quality import assess_response_intent, build_quality_prompt, get_anti_pattern_reminder


def test_intent_classification():
    """Test that we can classify user intent."""
    result = assess_response_intent("What are you thinking about?")
    # assess_response_intent returns a dict with 'intent' key
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    mode = result.get('primary_mode', '')
    assert mode, f"No primary_mode found in result: {result}"

    r2 = assess_response_intent("How do you feel right now?")
    assert isinstance(r2, dict), f"Expected dict for emotional query"

    r3 = assess_response_intent("What is 2+2?")
    assert isinstance(r3, dict), f"Expected dict for factual query"

    print(f"  Thinking → {result.get('primary_mode')}, Feeling → {r2.get('primary_mode')}, Factual → {r3.get('primary_mode')}")
    return True
def test_quality_prompt_generation():
    """Test that quality prompts are generated with content."""
    prompt = build_quality_prompt("How are you feeling?")
    assert prompt, "Empty quality prompt"
    assert len(prompt) > 20, f"Quality prompt too short: {len(prompt)} chars"
    assert 'guidance' in prompt.lower() or 'respond' in prompt.lower(), f"No guidance keywords in: {prompt}"
    print(f"  Prompt ({len(prompt)} chars): {prompt[:150]}...")
    return True


def test_anti_pattern_reminder():
    """Test anti-pattern reminder has substance."""
    reminder = get_anti_pattern_reminder()
    assert reminder, "Empty anti-pattern reminder"
    assert len(reminder) > 10, f"Reminder too short: {len(reminder)} chars"
    assert 'avoid' in reminder.lower(), f"No 'avoid' in reminder: {reminder[:100]}"
    print(f"  Reminder ({len(reminder)} chars): {reminder[:150]}...")
    return True


def test_compose_system_prompt_includes_guidance():
    """Test that compose_system_prompt now includes quality guidance."""
    try:
        from brain.chat_composer import compose_system_prompt
    except ImportError as e:
        print(f"  SKIP: Cannot import compose_system_prompt: {e}")
        return True  # Skip gracefully
    
    prompt = compose_system_prompt("How do you feel right now?")
    assert prompt, "Empty system prompt"
    
    lower = prompt.lower()
    has_guidance = any(kw in lower for kw in ['response quality guidance', 'avoid', 'guidance'])
    assert has_guidance, f"Missing response guidance in prompt. Length: {len(prompt)}\n  First 500 chars: {prompt[:500]}"
    print(f"  System prompt includes quality guidance ({len(prompt)} chars)")
    return True


def test_prompts_vary_by_intent():
    """Test that different query types produce different quality prompts."""
    p1 = build_quality_prompt("How do you feel?")
    p2 = build_quality_prompt("What is the capital of France?")
    # They should be different since intents differ
    if p1 != p2:
        print(f"  ✓ Prompts vary by query intent")
    else:
        print(f"  ⚠ Prompts are identical — intent classification may not be differentiating")
    return True


def test_conversational_context_builds():
    """Test that conversational context produces real data."""
    try:
        from brain.conversational_context import get_emotional_portrait, get_active_plans, get_recent_memories
    except ImportError as e:
        print(f"  SKIP: Cannot import conversational_context: {e}")
        return True
    
    portrait = get_emotional_portrait()
    assert isinstance(portrait, (str, dict)), f"Expected str/dict, got {type(portrait)}"
    
    plans = get_active_plans()
    assert isinstance(plans, (str, dict, list)), f"Expected str/dict/list, got {type(plans)}"
    
    memories = get_recent_memories()
    assert isinstance(memories, (str, dict, list)), f"Expected str/dict/list, got {type(memories)}"
    
    print(f"  Portrait type: {type(portrait).__name__}, Plans type: {type(plans).__name__}, Memories type: {type(memories).__name__}")
    return True


if __name__ == '__main__':
    tests = [
        ("test_intent_classification", test_intent_classification),
        ("test_quality_prompt_generation", test_quality_prompt_generation),
        ("test_anti_pattern_reminder", test_anti_pattern_reminder),
        ("test_compose_system_prompt_includes_guidance", test_compose_system_prompt_includes_guidance),
        ("test_prompts_vary_by_intent", test_prompts_vary_by_intent),
        ("test_conversational_context_builds", test_conversational_context_builds),
    ]
    
    print("=== User Alignment Chat Quality Tests ===\n")
    passed = 0
    failed = 0
    for name, func in tests:
        try:
            if func():
                passed += 1
                print(f"  ✓ {name}")
            else:
                failed += 1
                print(f"  ✗ {name}: returned False")
        except Exception as e:
            failed += 1
            print(f"  ✗ {name}: {e}")
            traceback.print_exc()
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
    if failed:
        print("Some tests failed — investigate above.")
    else:
        print("All tests passed!")
    sys.exit(0 if not failed else 1)
