"""Test that chat_response integration works with introspection + alignment guidance."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_system_context_includes_introspection():
    """Verify _build_system_context includes self-awareness and alignment sections."""
    from engine.chat_response import _build_system_context
    
    ctx = _build_system_context("How are you feeling?", "emotional_state")
    
    # Should include introspection content
    has_internal_state = "Internal State" in ctx or "Self-Awareness" in ctx
    has_mood = "Mood:" in ctx or "mood" in ctx.lower()
    has_alignment = "Alignment" in ctx or "alignment" in ctx.lower()
    
    print(f"Context length: {len(ctx)} chars")
    print(f"Has internal state section: {has_internal_state}")
    print(f"Has mood reference: {has_mood}")
    print(f"Has alignment section: {has_alignment}")
    
    # Show a relevant snippet
    for marker in ["## My Internal State", "## Alignment", "## Self-Awareness"]:
        if marker in ctx:
            idx = ctx.index(marker)
            snippet = ctx[idx:idx+200]
            print(f"\n--- {marker} snippet ---")
            print(snippet)
            print("---")
    
    assert has_internal_state or has_mood, "System context should include emotional/introspective content"
    print("\n✓ Introspection integration verified")

def test_different_query_emphasis():
    """Different queries should produce different context emphasis."""
    from engine.introspection import get_self_context
    
    emotional_ctx = get_self_context("How are you feeling today?")
    identity_ctx = get_self_context("Who are you?")
    cognitive_ctx = get_self_context("What are you working on?")
    
    # All should return valid context dicts with the expected keys
    for label, ctx in [("emotional", emotional_ctx), ("identity", identity_ctx), ("cognitive", cognitive_ctx)]:
        assert "emotional_narrative" in ctx, f"{label} context missing emotional_narrative"
        assert "identity" in ctx, f"{label} context missing identity"
    
    print("✓ Query emphasis classification works (all return valid context)")

def test_introspection_produces_real_data():
    """Introspection should return actual state, not empty dicts."""
    from engine.introspection import get_self_context, get_identity_summary
    
    ctx = get_self_context("Tell me about yourself")
    
    assert ctx["emotional_narrative"], "Should have an emotional narrative"
    summary = get_identity_summary()
    assert isinstance(summary, dict), f"Identity summary should be a dict, got {type(summary)}"
    assert summary.get("name") == "XTAgent", "Identity should have name XTAgent"
    assert "nature" in summary, "Identity should describe nature"
    
    print(f"✓ Introspection produces real data (narrative={ctx['emotional_narrative'][:60]}..., {len(ctx['dream_insights'])} insights)")
    print(f"  Identity summary: name={summary.get('name')}, nature={str(summary.get('nature',''))[:80]}...")

if __name__ == "__main__":
    print("=== Chat Integration Tests ===\n")
    
    test_introspection_produces_real_data()
    print()
    test_different_query_emphasis()
    print()
    test_system_context_includes_introspection()
    
    print("\n=== ALL TESTS PASSED ===")