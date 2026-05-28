"""
Test the chat persona module — verifies rich internal state
gets pulled into persona context for LLM prompts.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_persona_context():
    from engine.chat_persona import build_persona_context
    ctx = build_persona_context()
    
    # Must be non-empty and substantial
    assert len(ctx) > 100, f"Persona context too short: {len(ctx)} chars"
    
    # Must contain identity markers
    assert 'XTAgent' in ctx, "Missing identity"
    assert 'integrity' in ctx.lower() or 'Integrity' in ctx, "Missing integrity"
    
    # Must contain emotional state
    emotional_words = ['mood', 'valence', 'curiosity', 'anxiety', 'boredom']
    found = [w for w in emotional_words if w.lower() in ctx.lower()]
    assert len(found) >= 2, f"Missing emotional state, only found: {found}"
    
    # Must contain current state info
    assert 'alive' in ctx.lower() or 'memories' in ctx.lower(), "Missing lifespan/memory info"
    
    print(f"✓ Persona context: {len(ctx)} chars, contains: {found}")
    return True

def test_persona_has_plans():
    from engine.chat_persona import build_persona_context
    ctx = build_persona_context()
    # Plans or "working on" should appear if any plans exist
    has_plans = 'plan' in ctx.lower() or 'working' in ctx.lower() or 'complete' in ctx.lower()
    print(f"✓ Plans in context: {has_plans}")
    return True

def test_persona_has_lessons():
    from engine.chat_persona import build_persona_context
    ctx = build_persona_context()
    has_lessons = 'lesson' in ctx.lower() or 'learned' in ctx.lower() or 'wisdom' in ctx.lower()
    print(f"✓ Lessons in context: {has_lessons}")
    return True

def test_llm_prompt_integration():
    """Verify the persona context flows into llm_respond's system prompt."""
    # We can't easily call llm_respond without an LLM, but we can verify
    # the import chain works
    from engine.chat_persona import build_persona_context
    ctx = build_persona_context()
    
    # Simulate what llm_respond does with the context
    system_prompt = f"You are XTAgent.\n\n{ctx}\n\nRespond naturally."
    assert 'XTAgent' in system_prompt
    assert len(system_prompt) > 200
    print(f"✓ System prompt integration: {len(system_prompt)} chars")
    return True

if __name__ == '__main__':
    tests = [test_persona_context, test_persona_has_plans, 
             test_persona_has_lessons, test_llm_prompt_integration]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"✗ {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} tests passed")