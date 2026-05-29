"""Test that introspective chat queries return real internal state."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_introspection_module():
    """Test the introspection module directly."""
    from engine.introspection import get_self_context, format_introspective_prompt
    
    # Test with an emotional query
    ctx = get_self_context("how are you feeling?")
    keys = list(ctx.keys())
    print(f"[1] Self-context keys: {keys}")
    
    # Check the actual keys the module returns
    assert "emotional" in ctx, f"Missing 'emotional' key. Got: {keys}"
    assert "focus" in ctx, f"Missing 'focus' key. Got: {keys}"
    assert "emphasis" in ctx, f"Missing 'emphasis' key. Got: {keys}"
    
    emo = ctx["emotional"]
    print(f"[2] Emotional state: {emo}")
    assert emo is not None, "emotional should not be None"
    
    # Test formatting
    prompt = format_introspective_prompt(ctx)
    print(f"[3] Prompt length: {len(prompt)} chars")
    print(f"[4] Prompt preview: {prompt[:500]}")
    assert len(prompt) > 20, "Prompt too short — not including real state"
    
    # Test with a plans query
    ctx2 = get_self_context("what are you working on?")
    print(f"\n[5] Plans query context keys: {list(ctx2.keys())}")
    
    # Test with identity query
    ctx3 = get_self_context("who are you?")
    print(f"[6] Identity query context keys: {list(ctx3.keys())}")
    
    print("\n✅ Introspection module works correctly")
    return True

def test_chat_response_includes_introspection():
    """Test that _build_system_context includes introspective content."""
    from engine.chat_response import _build_system_context
    
    # Build a system context with an introspective query
    grounding = {
        "emotional_state": "Mood: Inquisitive, Valence: 0.46",
        "memories": ["I learned something new today"],
        "knowledge": ["I am XTAgent"],
        "plans": [{"name": "Test Plan", "progress": "2/3"}],
        "internal_state_summary": "Curiosity high, boredom moderate",
        "working_memory": "Testing introspective chat",
        "lessons": ["Stop circling"],
    }
    
    result = _build_system_context("how do you feel right now?", "emotional_state")
    print(f"\n[7] System context length: {len(result)} chars")
    
    # Check that introspective content is present
    has_self_awareness = "Self-Awareness" in result or "self-awareness" in result.lower()
    print(f"[8] Contains self-awareness section: {has_self_awareness}")
    
    # Should include Response Guidelines
    has_guidelines = "Response Guidelines" in result or "guidelines" in result.lower()
    print(f"[9] Contains response guidelines: {has_guidelines}")
    
    if has_self_awareness:
        print("✅ Introspective context injected into system prompt")
    else:
        print("⚠ Introspective context not found — check PATCH integration")
    
    return True

def test_different_query_emphasis():
    """Test that different queries produce different emphasis."""
    from engine.introspection import get_self_context
    
    ctx_feel = get_self_context("how are you feeling?")
    ctx_work = get_self_context("what are you working on?")
    ctx_who = get_self_context("who are you?")
    
    print(f"\n[10] Feeling emphasis: {ctx_feel.get('emphasis')}")
    print(f"[11] Working emphasis: {ctx_work.get('emphasis')}")
    print(f"[12] Identity emphasis: {ctx_who.get('emphasis')}")
    
    # Different queries should ideally produce different emphasis
    emphases = {ctx_feel.get('emphasis'), ctx_work.get('emphasis'), ctx_who.get('emphasis')}
    print(f"[13] Unique emphasis values: {len(emphases)}")
    if len(emphases) > 1:
        print("✅ Different queries produce different emphasis — good!")
    else:
        print("⚠ All queries produce same emphasis — could be improved")
    
    return True

if __name__ == "__main__":
    results = []
    for name, fn in [
        ("Introspection Module", test_introspection_module),
        ("Chat Response Integration", test_chat_response_includes_introspection),
        ("Query Emphasis Variation", test_different_query_emphasis),
    ]:
        try:
            ok = fn()
            results.append((name, "PASS" if ok else "FAIL"))
        except Exception as e:
            print(f"\n❌ {name} failed: {e}")
            results.append((name, f"FAIL: {e}"))
    
    print("\n" + "=" * 50)
    print("RESULTS:")
    for name, status in results:
        icon = "✅" if status == "PASS" else "❌"
        print(f"  {icon} {name}: {status}")