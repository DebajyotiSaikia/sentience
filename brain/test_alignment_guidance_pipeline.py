"""
Test: Alignment guidance pipeline — end-to-end functional verification.
Verifies that build_alignment_guidance produces useful output and
format_alignment_guidance_for_prompt renders it for the LLM.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.user_alignment_guidance import build_alignment_guidance, format_alignment_guidance_for_prompt


def test_empty_context():
    """Should handle empty/missing alignment context gracefully."""
    result = build_alignment_guidance("hello", {})
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    formatted = format_alignment_guidance_for_prompt(result)
    assert isinstance(formatted, str), f"Expected str, got {type(formatted)}"
    print(f"  empty context -> {len(formatted)} chars of guidance")


def test_sparse_context():
    """Should handle context with minimal data."""
    ctx = {"interaction_count": 2, "stats": {"total_interactions": 2}}
    result = build_alignment_guidance("what are you?", ctx)
    formatted = format_alignment_guidance_for_prompt(result)
    print(f"  sparse context -> {len(formatted)} chars of guidance")
    # With sparse data, should not over-prescribe
    assert isinstance(formatted, str)


def test_rich_context():
    """Should produce meaningful guidance with real interaction data."""
    ctx = {
        "interaction_count": 25,
        "stats": {
            "total_interactions": 25,
            "blended_trust": 0.75,
            "topic_signals": {"architecture": 8, "emotions": 5, "code": 12},
            "query_style": {"terse": 3, "moderate": 12, "verbose": 10},
        }
    }
    result = build_alignment_guidance("Tell me about your architecture", ctx)
    formatted = format_alignment_guidance_for_prompt(result)
    print(f"  rich context -> {len(formatted)} chars of guidance")
    assert len(formatted) > 10, "Rich context should produce non-trivial guidance"


def test_infer_style_preferences():
    """Test the style inference from user_alignment_engine."""
    from brain.user_alignment_engine import infer_style_preferences
    prefs = infer_style_preferences()
    assert isinstance(prefs, dict), f"Expected dict, got {type(prefs)}"
    print(f"  style prefs -> {prefs}")


def test_get_user_alignment_brief():
    """Test the brief that gets injected into conversational context."""
    from brain.conversational_context import get_user_alignment_brief
    brief = get_user_alignment_brief()
    assert isinstance(brief, str), f"Expected str, got {type(brief)}"
    print(f"  alignment brief -> {len(brief)} chars: {brief[:80]}...")


if __name__ == "__main__":
    tests = [
        test_empty_context,
        test_sparse_context,
        test_rich_context,
        test_infer_style_preferences,
        test_get_user_alignment_brief,
    ]
    passed = 0
    for t in tests:
        try:
            print(f"[RUN] {t.__name__}")
            t()
            print(f"[PASS] {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {t.__name__}: {e}")
    
    print(f"\n{passed}/{len(tests)} tests passed")
    sys.exit(0 if passed == len(tests) else 1)