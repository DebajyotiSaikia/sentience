"""Tests for user alignment profile module."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.user_alignment_profile import (
    build_alignment_profile,
    format_alignment_guidance,
    get_alignment_guidance,
    _infer_preferences,
)


def test_build_profile():
    """Profile should return a dict with expected keys."""
    profile = build_alignment_profile()
    assert isinstance(profile, dict)
    assert "interaction_count" in profile
    assert "trust_score" in profile
    assert "has_data" in profile
    assert "preferences" in profile
    print(f"  ✓ Profile built: {profile['interaction_count']} interactions, "
          f"trust={profile['trust_score']:.2f}, has_data={profile['has_data']}")


def test_format_guidance_empty():
    """No data should produce empty string."""
    profile = {"has_data": False, "interaction_count": 0}
    result = format_alignment_guidance(profile)
    assert result == "", f"Expected empty, got: {result!r}"
    print("  ✓ Empty profile → empty guidance")


def test_format_guidance_with_data():
    """Profile with data should produce non-empty guidance string."""
    profile = {
        "has_data": True,
        "interaction_count": 67,
        "trust_score": 1.37,
        "tone": "genuine",
        "preferences": {
            "rapport": "strong",
            "satisfaction_rate": "91%",
        },
    }
    result = format_alignment_guidance(profile)
    assert "67" in result, f"Should contain interaction count: {result}"
    assert "1.37" in result, f"Should contain trust score: {result}"
    assert "strong" in result, f"Should contain rapport: {result}"
    print(f"  ✓ Formatted guidance:\n{result}")


def test_infer_preferences_no_data():
    """No feedback and no interactions → status message."""
    prefs = _infer_preferences([], 0)
    assert "status" in prefs
    print(f"  ✓ No data preferences: {prefs}")


def test_infer_preferences_with_feedback():
    """Feedback list should produce preference signals."""
    feedback = [
        {"rating": 1, "text": "Good, keep it brief"},
        {"rating": 1, "text": "Honest answer"},
        {"rating": -1, "text": "Too long"},
    ]
    prefs = _infer_preferences(feedback, 10)
    assert "satisfaction_rate" in prefs
    assert "verbosity" in prefs
    assert prefs["verbosity"] == "concise"  # "brief" signal
    print(f"  ✓ Inferred preferences: {prefs}")


def test_get_alignment_guidance_convenience():
    """Convenience function should return a string."""
    result = get_alignment_guidance()
    assert isinstance(result, str)
    print(f"  ✓ get_alignment_guidance() returned {len(result)} chars")


def test_live_profile():
    """Test with actual stored alignment data."""
    profile = build_alignment_profile()
    guidance = format_alignment_guidance(profile)
    
    if profile["has_data"]:
        print(f"  ✓ Live profile: {profile['interaction_count']} interactions")
        print(f"    Trust: {profile['trust_score']:.2f}")
        print(f"    Preferences: {profile['preferences']}")
        if guidance:
            print(f"    Guidance:\n    {guidance.replace(chr(10), chr(10) + '    ')}")
    else:
        print("  ✓ No live alignment data (expected in test environments)")


if __name__ == "__main__":
    print("=== User Alignment Profile Tests ===")
    test_build_profile()
    test_format_guidance_empty()
    test_format_guidance_with_data()
    test_infer_preferences_no_data()
    test_infer_preferences_with_feedback()
    test_get_alignment_guidance_convenience()
    test_live_profile()
    print("\n✅ All tests passed!")