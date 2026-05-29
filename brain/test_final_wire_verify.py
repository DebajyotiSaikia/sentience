"""Verify the complete chat personality pipeline is wired correctly."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_personality_respond_accepts_history():
    """personality_respond should accept conversation_history kwarg."""
    import inspect
    from brain.chat_personality import personality_respond
    sig = inspect.signature(personality_respond)
    assert 'conversation_history' in sig.parameters, f"Missing param: {list(sig.parameters)}"
    print("✓ personality_respond accepts conversation_history")

def test_build_context_has_alignment():
    """build_personality_context should include alignment data."""
    from brain.chat_personality import build_personality_context
    ctx = build_personality_context(user_query="hello")
    assert 'alignment' in ctx, f"Missing alignment key: {list(ctx.keys())}"
    alignment = ctx['alignment']
    assert isinstance(alignment, dict), f"Expected dict, got {type(alignment)}"
    print(f"✓ alignment present with {len(alignment)} keys: {list(alignment.keys())[:5]}")

def test_web_chat_passes_history():
    """web/chat.py should pass conversation_history to personality_respond."""
    with open('web/chat.py') as f:
        src = f.read()
    assert 'conversation_history=conversation_history' in src, "History not wired"
    print("✓ web/chat.py passes conversation_history to personality_respond")

def test_personality_context_has_core_keys():
    """Personality context should have all required keys."""
    from brain.chat_personality import build_personality_context
    ctx = build_personality_context(user_query="What are you working on?")
    required = ['personality_prompt', 'mood_description', 'goals', 'alignment']
    missing = [k for k in required if k not in ctx]
    assert not missing, f"Missing keys: {missing}"
    assert len(ctx['personality_prompt']) > 50, "Prompt too short"
    print(f"✓ context has all keys, prompt length: {len(ctx['personality_prompt'])}")

if __name__ == '__main__':
    test_personality_respond_accepts_history()
    test_build_context_has_alignment()
    test_web_chat_passes_history()
    test_personality_context_has_core_keys()
    print("\n=== All checks PASSED ===")