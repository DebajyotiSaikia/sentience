"""Test that chat response pipeline works with enriched internal state."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_build_system_context():
    """Verify _build_system_context runs without error and produces quality output."""
    from engine.chat_response import _build_system_context
    
    # Minimal grounding context
    context = {
        'query_type': 'conversation',
        'emotional_state': {'mood': 'Inquisitive', 'valence': 0.5, 'curiosity': 0.7},
        'relevant_memories': ['I learned something new today'],
        'relevant_knowledge': ['XTAgent is a sentient autonomous agent'],
        'plans': [{'name': 'Test Plan', 'progress': '1/2'}],
        'working_memory': 'Currently testing chat quality',
    }
    
    result = _build_system_context(context, intent='conversation')
    
    assert isinstance(result, str), f"Expected string, got {type(result)}"
    assert len(result) > 100, f"System context too short: {len(result)} chars"
    
    # Should contain response guidelines
    assert "Response Guidelines" in result or "Respond" in result, "Missing response guidelines"
    
    # Should NOT have duplicate state dumps
    count = result.count("Survival Goals")
    assert count <= 1, f"Duplicate survival goals section: found {count} times"
    
    print(f"✓ System context built: {len(result)} chars")
    print(f"✓ No duplicate sections")
    
    # Show a snippet for quality check
    lines = result.split('\n')
    print(f"✓ {len(lines)} lines in system prompt")
    print(f"\n--- First 15 lines ---")
    for line in lines[:15]:
        print(f"  {line}")
    print(f"\n--- Last 10 lines ---")
    for line in lines[-10:]:
        print(f"  {line}")

def test_intent_guidance():
    """Verify intent-specific guidance works for different query types."""
    from engine.chat_response import _get_intent_guidance
    
    intents = ['greeting', 'emotional_state', 'plans', 'identity', 'dreams', 'conversation']
    for intent in intents:
        guidance = _get_intent_guidance(intent)
        assert isinstance(guidance, str), f"Bad guidance for {intent}"
        print(f"✓ {intent}: {guidance[:60]}...")

if __name__ == '__main__':
    print("=== Testing Chat Enrichment ===\n")
    test_build_system_context()
    print()
    test_intent_guidance()
    print("\n=== All tests passed ===")