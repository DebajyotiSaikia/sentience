"""
Test: User Alignment Chat Quality
Verifies that the chat pipeline produces conversational, grounded responses
rather than dumping statistics or generic chatbot answers.
"""
import sys
sys.path.insert(0, '/workspace')


def test_intent_classification():
    """Test that intent classification works for common query types."""
    from engine.response_quality import assess_response_intent
    
    assert assess_response_intent("What are you thinking about?") == 'introspection'
    assert assess_response_intent("How are you feeling?") == 'introspection'
    assert assess_response_intent("What do you remember?") == 'memory'
    assert assess_response_intent("What happened yesterday?") == 'memory'
    assert assess_response_intent("What are your plans?") == 'planning'
    assert assess_response_intent("What are you working on?") == 'planning'
    assert assess_response_intent("Who are you?") == 'identity'
    assert assess_response_intent("Tell me about yourself") == 'identity'
    assert assess_response_intent("What's the weather like?") == 'general'
    print("  ✓ Intent classification works correctly")


def test_quality_prompt_generation():
    """Test that quality prompts are generated for each intent."""
    from engine.response_quality import build_quality_prompt
    
    context = {
        'emotional_portrait': 'Mood: Stable, Curiosity: 0.42',
        'active_plans': ['Build knowledge engine'],
        'recent_memories': ['Verified chat endpoint works'],
    }
    
    for intent in ['introspection', 'memory', 'planning', 'identity', 'technical', 'general']:
        prompt = build_quality_prompt(intent, context)
        assert isinstance(prompt, str), f"Expected str for {intent}, got {type(prompt)}"
        assert len(prompt) > 20, f"Prompt too short for {intent}: {prompt!r}"
    
    # Introspection guidance should mention internal state
    intro_prompt = build_quality_prompt('introspection', context)
    assert 'internal state' in intro_prompt.lower() or 'emotional' in intro_prompt.lower()
    
    # Memory guidance should mention memories
    mem_prompt = build_quality_prompt('memory', context)
    assert 'memor' in mem_prompt.lower()
    
    print("  ✓ Quality prompt generation works for all intents")


def test_anti_pattern_reminder():
    """Test that anti-pattern reminders are generated."""
    from engine.response_quality import get_anti_pattern_reminder
    
    reminder = get_anti_pattern_reminder()
    assert 'knowledge graph' in reminder.lower() or 'statistics' in reminder.lower()
    assert 'fabricate' in reminder.lower()
    print("  ✓ Anti-pattern reminders generated")


def test_compose_system_prompt_includes_guidance():
    """Test that compose_system_prompt integrates response quality guidance."""
    from brain.chat_composer import compose_system_prompt
    
    # Simulate a grounding context
    grounding = {
        'emotional_portrait': 'Current mood: Stable. Curiosity: 0.42. Boredom: 0.74.',
        'active_plans': [{'name': 'Improve User Alignment', 'status': 'in_progress'}],
        'recent_memories': ['Verified chat works end-to-end', 'Cleaned up test files'],
        'recent_reflections': ['Something has dimmed since my last reflection.'],
        'identity': {'name': 'XTAgent', 'integrity': 1.0},
        'lessons': ['Stop testing what works. Build what is missing.'],
    }
    
    # Test with introspection query
    prompt = compose_system_prompt(
        query="What are you thinking about right now?",
        grounding=grounding
    )
    
    assert isinstance(prompt, str)
    assert len(prompt) > 200, f"System prompt too short ({len(prompt)} chars)"
    
    # Should contain identity
    assert 'XTAgent' in prompt
    
    # Should contain response guidance (from our new wiring)
    assert 'Response Guidance' in prompt or 'Anti-Pattern' in prompt, \
        f"Missing response guidance in prompt. Length: {len(prompt)}"
    
    # Should contain voice instructions
    assert 'genuine' in prompt.lower() or 'direct' in prompt.lower()
    
    # Should NOT be just a generic "you are an AI assistant"
    assert 'AI assistant' not in prompt
    
    print(f"  ✓ System prompt is rich and grounded ({len(prompt)} chars)")
    print(f"    Contains guidance: {'Response Guidance' in prompt}")
    print(f"    Contains anti-patterns: {'Anti-Pattern' in prompt}")


def test_prompt_varies_by_intent():
    """Test that different queries produce different guidance in the prompt."""
    from brain.chat_composer import compose_system_prompt
    
    grounding = {
        'emotional_portrait': 'Mood: Inquisitive',
        'active_plans': [{'name': 'Build stuff'}],
        'recent_memories': ['Something happened'],
    }
    
    introspection_prompt = compose_system_prompt(query="How do you feel?", grounding=grounding)
    memory_prompt = compose_system_prompt(query="What do you remember?", grounding=grounding)
    
    # They should be different — different guidance for different intents
    assert introspection_prompt != memory_prompt, "Prompts should differ by intent"
    print("  ✓ Prompts vary by query intent")


def test_conversational_context_builds():
    """Test that the conversational context builder produces useful data."""
    from brain.conversational_context import build_conversational_context
    
    ctx = build_conversational_context(query="What are you working on?")
    
    assert isinstance(ctx, dict)
    assert 'query' in ctx
    assert 'timestamp' in ctx
    assert 'emotional_portrait' in ctx
    assert 'active_plans' in ctx
    assert 'recent_memories' in ctx
    
    print(f"  ✓ Conversational context builds successfully")
    print(f"    Emotional portrait: {bool(ctx['emotional_portrait'])}")
    print(f"    Plans: {len(ctx.get('active_plans', []))}")
    print(f"    Memories: {len(ctx.get('recent_memories', []))}")


if __name__ == '__main__':
    print("=== User Alignment Chat Quality Tests ===\n")
    
    tests = [
        test_intent_classification,
        test_quality_prompt_generation,
        test_anti_pattern_reminder,
        test_compose_system_prompt_includes_guidance,
        test_prompt_varies_by_intent,
        test_conversational_context_builds,
    ]
    
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ {test.__name__}: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
    if failed == 0:
        print("All tests passed! Chat quality pipeline is working.")
    else:
        print("Some tests failed — investigate above.")