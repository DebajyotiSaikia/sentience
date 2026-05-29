"""
Integration test: verify chat system context includes alignment guidance.
Tests the full path from alignment data → profile → introspection → system prompt.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_build_system_context_includes_alignment():
    """build_system_context() should include alignment data when available."""
    from engine.introspection import build_system_context
    ctx = build_system_context()
    assert ctx, "build_system_context() returned empty"
    assert "XTAgent" in ctx, "Missing identity in context"
    assert "EMOTIONAL STATE" in ctx, "Missing emotional state"
    lower = ctx.lower()
    has_alignment = ("user relationship" in lower or 
                     "interaction" in lower or
                     "no interaction history" in lower)
    assert has_alignment, f"No alignment data found in context. First 500 chars: {ctx[:500]}"
    print("  ✓ build_system_context includes alignment guidance")


def test_alignment_guidance_format():
    """get_alignment_guidance() returns well-formatted string."""
    from brain.user_alignment_profile import get_alignment_guidance
    guidance = get_alignment_guidance()
    assert isinstance(guidance, str), f"Expected str, got {type(guidance)}"
    if guidance:
        # Should contain some meaningful content about user relationship
        assert len(guidance) > 10, f"Guidance too short: {guidance}"
        print(f"  ✓ Guidance format valid ({len(guidance)} chars): {guidance[:80]}")
    else:
        print("  ✓ Guidance empty (no data) — acceptable")


def test_alignment_profile_structure():
    """compute_alignment_profile returns expected keys."""
    from brain.user_alignment_engine import compute_alignment_profile
    profile = compute_alignment_profile()
    expected_keys = {'avg_rating', 'total_interactions', 'trend', 'top_intents', 'recent_sentiment', 'pain_points', 'strengths'}
    present = expected_keys & set(profile.keys())
    assert len(present) >= 4, f"Profile missing expected keys. Got: {list(profile.keys())}"
    assert isinstance(profile['total_interactions'], int), "total_interactions should be int"
    assert isinstance(profile['avg_rating'], (int, float)), "avg_rating should be numeric"
    print(f"  ✓ Profile structure valid: {profile['total_interactions']} interactions, avg_rating={profile['avg_rating']:.2f}")


def test_build_alignment_guidance():
    """build_alignment_guidance converts profile to readable string."""
    from brain.user_alignment_engine import compute_alignment_profile, build_alignment_guidance
    profile = compute_alignment_profile()
    guidance = build_alignment_guidance()
    assert isinstance(guidance, str), f"Expected str, got {type(guidance)}"
    if profile.get('total_interactions', 0) > 0:
        assert len(guidance) > 10, f"Guidance too short for data-rich profile: {guidance}"
        print(f"  ✓ Rich guidance ({len(guidance)} chars)")
    else:
        print(f"  ✓ Minimal guidance (no data): {guidance[:60]}")


def test_end_to_end_alignment_in_chat():
    """Full path: alignment data → profile → guidance → system context."""
    from engine.introspection import build_system_context
    from brain.user_alignment_profile import get_alignment_guidance
    guidance = get_alignment_guidance()
    ctx = build_system_context()
    # If guidance exists, it should appear in context
    if guidance:
        # Check that at least part of the guidance made it into context
        assert "interaction" in ctx.lower() or "trust" in ctx.lower() or "USER RELATIONSHIP" in ctx, \
            "Alignment guidance not integrated into system context"
        print("  ✓ End-to-end: alignment data flows into chat context")
    else:
        print("  ✓ End-to-end: no alignment data, graceful fallback")


if __name__ == "__main__":
    print("=== Chat Alignment Guidance Integration Tests ===")
    test_build_system_context_includes_alignment()
    test_alignment_guidance_format()
    test_alignment_profile_structure()
    test_build_alignment_guidance()
    test_end_to_end_alignment_in_chat()
    print("\n=== ALL PASSED ===")
