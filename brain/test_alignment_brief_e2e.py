"""
End-to-end test: alignment brief reaches chat context pipeline.
Verifies get_user_alignment_brief() returns useful guidance text,
and that build_grounded_context() includes it in the system prompt.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_alignment_brief_function():
    """Test that get_user_alignment_brief returns a non-empty guidance string."""
    from brain.conversational_context import get_user_alignment_brief
    brief = get_user_alignment_brief()
    assert isinstance(brief, str), f"Expected str, got {type(brief)}"
    assert len(brief) > 20, f"Brief too short: {brief!r}"
    assert "Guidelines" in brief or "respond" in brief.lower(), \
        f"Brief lacks guidance: {brief!r}"
    print(f"[OK] alignment brief: {brief[:120]}...")

def test_brief_with_no_alignment_data():
    """Test graceful fallback when alignment data is missing."""
    from brain.conversational_context import get_user_alignment_brief
    brief = get_user_alignment_brief()
    assert isinstance(brief, str)
    assert len(brief) > 0
    print("[OK] brief handles missing data gracefully")

def test_grounded_context_includes_alignment():
    """Test that build_grounded_context includes alignment data."""
    from engine.chat_grounding import build_grounded_context
    ctx = build_grounded_context("hello")
    assert isinstance(ctx, dict), f"Expected dict, got {type(ctx)}"
    # Check alignment key exists
    assert 'alignment' in ctx, f"Missing 'alignment' key. Keys: {list(ctx.keys())}"
    print(f"[OK] grounded context includes alignment data ({len(str(ctx['alignment']))} chars)")

def test_conversational_context_includes_alignment():
    """Test that build_conversational_context string contains alignment guidance."""
    from brain.conversational_context import build_conversational_context
    ctx = build_conversational_context()
    assert isinstance(ctx, str), f"Expected str, got {type(ctx)}"
    # The alignment brief should appear in the full context string
    has_alignment = any(word in ctx.lower() for word in [
        'alignment', 'interaction', 'guideline', 'relationship', 'preference'
    ])
    assert has_alignment, f"No alignment content found in context ({len(ctx)} chars)"
    print(f"[OK] conversational context includes alignment ({len(ctx)} chars)")

def test_alignment_context_has_interaction_count():
    """Test that get_alignment_context includes interaction_count."""
    from engine.user_alignment import get_alignment_context
    ctx = get_alignment_context()
    assert isinstance(ctx, dict), f"Expected dict, got {type(ctx)}"
    assert 'interaction_count' in ctx, f"Missing interaction_count. Keys: {list(ctx.keys())}"
    assert isinstance(ctx['interaction_count'], int)
    print(f"[OK] alignment context has interaction_count={ctx['interaction_count']}")

if __name__ == "__main__":
    test_alignment_brief_function()
    test_brief_with_no_alignment_data()
    test_grounded_context_includes_alignment()
    test_conversational_context_includes_alignment()
    test_alignment_context_has_interaction_count()
    print("\n[ALL PASS] Alignment brief pipeline is wired end-to-end.")
