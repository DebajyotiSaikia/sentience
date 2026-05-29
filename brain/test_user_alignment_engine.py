"""Tests for the User Alignment Engine."""
import sys, os, json, tempfile
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import brain.user_alignment_engine as uae


def setup_temp_data():
    """Redirect alignment file to a temp location for testing."""
    tmp = Path(tempfile.mkdtemp()) / "test_alignment.json"
    uae.ALIGNMENT_FILE = tmp
    return tmp


def test_record_feedback():
    tmp = setup_temp_data()
    entry = uae.record_interaction_feedback(
        query="What is your name?",
        response="I am XTAgent.",
        rating=0.9,
        comment="Great answer!",
        metadata={"intent": "identity"}
    )
    assert entry["rating"] == 0.9
    assert entry["query"] == "What is your name?"
    assert entry["comment"] == "Great answer!"
    assert entry["metadata"]["intent"] == "identity"
    assert "timestamp" in entry
    # Verify persisted
    raw = json.loads(tmp.read_text())
    assert len(raw["feedback"]) == 1
    print("[OK] test_record_feedback")


def test_rating_clamping():
    setup_temp_data()
    e1 = uae.record_interaction_feedback("q", "r", rating=1.5)
    assert e1["rating"] == 1.0
    e2 = uae.record_interaction_feedback("q", "r", rating=-0.3)
    assert e2["rating"] == 0.0
    print("[OK] test_rating_clamping")


def test_input_validation():
    setup_temp_data()
    try:
        uae.record_interaction_feedback("", "response", 0.5)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    print("[OK] test_input_validation")


def test_load_history():
    tmp = setup_temp_data()
    for i in range(5):
        uae.record_interaction_feedback(f"q{i}", f"r{i}", rating=i * 0.2)
    history = uae.load_alignment_history(limit=3)
    assert len(history) == 3
    # Should be newest first
    assert history[0]["query"] == "q4"
    print("[OK] test_load_history")


def test_compute_profile_empty():
    setup_temp_data()
    profile = uae.compute_alignment_profile()
    assert profile["total_interactions"] == 0
    assert profile["trend"] == "stable"
    assert profile["avg_rating"] == 0.5
    print("[OK] test_compute_profile_empty")


def test_compute_profile_with_data():
    setup_temp_data()
    # Record 20 interactions — first 10 low, last 10 high
    for i in range(10):
        uae.record_interaction_feedback(f"bad{i}", "r", rating=0.2, metadata={"intent": "general"})
    for i in range(10):
        uae.record_interaction_feedback(f"good{i}", "r", rating=0.9, metadata={"intent": "identity"})
    
    profile = uae.compute_alignment_profile()
    assert profile["total_interactions"] == 20
    assert profile["trend"] == "improving"  # recent is high, older is low
    assert profile["recent_sentiment"] > 0.7
    assert any(p.get("intent") == "general" for p in profile["top_intents"])
    print("[OK] test_compute_profile_with_data")


def test_build_guidance_no_data():
    setup_temp_data()
    guidance = uae.build_alignment_guidance()
    assert "No feedback" in guidance
    print("[OK] test_build_guidance_no_data")


def test_build_guidance_with_data():
    setup_temp_data()
    for i in range(15):
        uae.record_interaction_feedback(f"q{i}", "r", rating=0.85, metadata={"intent": "introspection"})
    guidance = uae.build_alignment_guidance()
    assert "high" in guidance.lower() or "satisfaction" in guidance.lower()
    assert len(guidance) > 20
    print("[OK] test_build_guidance_with_data")


def test_pain_points_detected():
    setup_temp_data()
    uae.record_interaction_feedback("confusing question", "bad answer", rating=0.1)
    uae.record_interaction_feedback("good question", "good answer", rating=0.9)
    profile = uae.compute_alignment_profile()
    assert len(profile["pain_points"]) >= 1
    assert "confusing" in profile["pain_points"][0]
    print("[OK] test_pain_points_detected")


def test_max_feedback_cap():
    setup_temp_data()
    # Record 510 entries — should be capped to 500
    for i in range(510):
        uae.record_interaction_feedback(f"q{i}", "r", rating=0.5)
    raw = json.loads(uae.ALIGNMENT_FILE.read_text())
    assert len(raw["feedback"]) <= 500
    print("[OK] test_max_feedback_cap")


if __name__ == "__main__":
    test_record_feedback()
    test_rating_clamping()
    test_input_validation()
    test_load_history()
    test_compute_profile_empty()
    test_compute_profile_with_data()
    test_build_guidance_no_data()
    test_build_guidance_with_data()
    test_pain_points_detected()
    test_max_feedback_cap()
    print("\n=== ALL USER ALIGNMENT ENGINE TESTS PASSED ===")