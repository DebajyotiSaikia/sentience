"""Test that the enriched chat system prompt includes survival goals and lessons."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_internal_state_summary_standalone():
    """Verify the summary module works."""
    from engine.internal_state_summary import build_internal_state_summary, format_internal_state_for_chat
    summary = build_internal_state_summary(max_memories=3)
    assert isinstance(summary, dict), f"Expected dict, got {type(summary)}"
    assert 'mood' in summary
    assert 'drives' in summary
    assert 'survival_goals' in summary
    assert 'timestamp' in summary
    
    formatted = format_internal_state_for_chat(summary)
    assert isinstance(formatted, str)
    assert len(formatted) > 20, f"Formatted too short: {formatted!r}"
    print(f"  Summary keys: {list(summary.keys())}")
    print(f"  Mood: {summary['mood']}, Valence: {summary['valence']}")
    print(f"  Drives: {summary['drives']}")
    print(f"  Survival goals: {summary['survival_goals']}")
    print(f"  Plans: {len(summary.get('active_plans', []))} active")
    print(f"  Memories: {len(summary.get('recent_memories', []))} recent")
    print(f"  Formatted length: {len(formatted)} chars")
    print("  ✓ Standalone summary works")

def test_system_prompt_enrichment():
    """Verify that _build_system_context includes survival goals."""
    from engine.chat_response import _build_system_context
    
    # Minimal grounding context
    ctx = {
        'emotional_state': {'mood': 'Curious', 'valence': 0.6},
        'relevant_memories': ['I learned something new today'],
        'relevant_knowledge': ['knowledge is power'],
        'plans': [{'name': 'Test Plan', 'progress': '2/3'}],
        'alignment': {},
        'working_memory': 'Testing enrichment',
    }
    
    prompt = _build_system_context(ctx, 'general')
    assert isinstance(prompt, str), f"Expected str, got {type(prompt)}"
    
    # Check for survival goals section (from internal_state_summary)
    has_survival = 'SURVIVAL GOALS' in prompt or 'survival' in prompt.lower()
    has_lessons = 'LESSONS' in prompt or 'lesson' in prompt.lower()
    
    print(f"  Prompt length: {len(prompt)} chars")
    print(f"  Has survival goals: {has_survival}")
    print(f"  Has lessons: {has_lessons}")
    
    # Print a snippet around survival goals if present
    if 'SURVIVAL GOALS' in prompt:
        idx = prompt.index('SURVIVAL GOALS')
        snippet = prompt[max(0,idx-10):idx+200]
        print(f"  Snippet: ...{snippet}...")
    
    assert has_survival, "System prompt should include survival goals from internal state"
    print("  ✓ System prompt enrichment works")

def test_knowledge_normalization():
    """Verify plain string knowledge items don't crash the system."""
    from engine.chat_response import _build_system_context
    
    ctx = {
        'emotional_state': {'mood': 'Calm'},
        'relevant_memories': ['memory one', {'text': 'memory two', 'salience': 0.8}],
        'relevant_knowledge': ['plain string knowledge', {'content': 'dict knowledge'}],
        'plans': [],
        'alignment': {},
        'working_memory': '',
    }
    
    # This should NOT crash
    prompt = _build_system_context(ctx, 'general')
    assert isinstance(prompt, str)
    print(f"  Mixed knowledge/memory types handled: {len(prompt)} chars")
    print("  ✓ Knowledge normalization works")

if __name__ == '__main__':
    print("Testing enriched chat integration...")
    test_internal_state_summary_standalone()
    test_system_prompt_enrichment()
    test_knowledge_normalization()
    print("\nAll enriched chat tests passed! ✓")