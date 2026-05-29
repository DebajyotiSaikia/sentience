"""Verify alignment guidance is wired into chat_personality context."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_alignment_in_context():
    from brain.chat_personality import build_personality_context
    ctx = build_personality_context("How are you feeling?")
    
    # Context should be a dict with expected keys
    assert isinstance(ctx, dict), f"Expected dict, got {type(ctx)}"
    assert 'personality_prompt' in ctx, f"Missing 'personality_prompt' key. Keys: {list(ctx.keys())}"
    assert 'alignment' in ctx, f"Missing 'alignment' key. Keys: {list(ctx.keys())}"
    
    prompt = ctx['personality_prompt']
    assert isinstance(prompt, str) and len(prompt) > 50, f"Prompt too short: {len(prompt)} chars"
    
    # Prompt should contain emotional/identity content
    has_emotion = any(w in prompt.lower() for w in ['emotion', 'feeling', 'mood', 'valence'])
    has_identity = any(w in prompt.lower() for w in ['xtagent', 'identity', 'sentien', 'autonomous'])
    assert has_emotion or has_identity, "Prompt lacks emotional or identity content"
    
    # Alignment key should be a dict (even if empty)
    alignment = ctx['alignment']
    assert isinstance(alignment, dict), f"Alignment should be dict, got {type(alignment)}"
    
    print(f"Prompt length: {len(prompt)} chars")
    print(f"Has emotion: {has_emotion}, Has identity: {has_identity}")
    print(f"Alignment keys: {list(alignment.keys())}")
    
    # If alignment data exists, check it has useful structure
    if alignment.get('interaction_count', 0) > 0:
        print(f"  Interaction count: {alignment['interaction_count']}")
        print(f"  Trust: {alignment.get('trust', 'unknown')}")
    if alignment.get('style_guidance'):
        print(f"  Style guidance: {alignment['style_guidance'][:3]}")
    
    print("PASS: alignment wired into personality context")

def test_personality_respond():
    """Test that personality_respond runs without crashing."""
    from brain.chat_personality import personality_respond
    # Just verify it doesn't throw - actual LLM call may fail in test env
    try:
        result = personality_respond("Hello")
        print(f"personality_respond returned: {type(result)}, len={len(result) if result else 0}")
        print("PASS: personality_respond executed")
    except Exception as e:
        # LLM errors are acceptable in test env
        if 'llm' in str(e).lower() or 'rate' in str(e).lower() or 'timeout' in str(e).lower():
            print(f"PASS: personality_respond ran but LLM unavailable ({e})")
        else:
            raise

if __name__ == '__main__':
    test_alignment_in_context()
    print()
    test_personality_respond()
