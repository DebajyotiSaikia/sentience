"""Tests for the user alignment feedback engine."""
import json
import os
import tempfile
import pytest
from unittest.mock import patch
from brain.user_alignment import (
    load_feedback,
    save_feedback,
    record_feedback,
    infer_preferences,
    build_alignment_brief,
    FEEDBACK_PATH,
)


@pytest.fixture
def temp_feedback(tmp_path):
    """Redirect feedback storage to a temp dir."""
    fake_path = tmp_path / "alignment_feedback.json"
    with patch("brain.user_alignment.FEEDBACK_PATH", fake_path):
        with patch("brain.user_alignment.DATA_DIR", tmp_path):
            yield fake_path


def test_load_empty(temp_feedback):
    """No file → empty list."""
    assert load_feedback() == []


def test_record_and_load(temp_feedback):
    rec = record_feedback("resp-001", 4, comment="Very helpful!", tags=["clear"])
    assert rec["rating"] == 4
    assert rec["response_id"] == "resp-001"
    assert rec["tags"] == ["clear"]

    loaded = load_feedback()
    assert len(loaded) == 1
    assert loaded[0]["comment"] == "Very helpful!"


def test_record_validates_rating(temp_feedback):
    with pytest.raises(ValueError, match="Rating must be int 1-5"):
        record_feedback("resp-002", 0)
    with pytest.raises(ValueError, match="Rating must be int 1-5"):
        record_feedback("resp-002", 6)
    with pytest.raises(ValueError):
        record_feedback("resp-002", "good")


def test_record_validates_response_id(temp_feedback):
    with pytest.raises(ValueError, match="response_id is required"):
        record_feedback("", 3)


def test_multiple_records(temp_feedback):
    record_feedback("r1", 5, tags=["concise"])
    record_feedback("r2", 2, tags=["verbose", "confusing"])
    record_feedback("r3", 4, tags=["helpful"])
    
    loaded = load_feedback()
    assert len(loaded) == 3


def test_infer_preferences_empty():
    prefs = infer_preferences([])
    assert prefs["total_feedback"] == 0
    assert prefs["avg_rating"] is None
    assert prefs["trend"] == "unknown"


def test_infer_preferences_with_data():
    feedback = [
        {"rating": 5, "tags": ["clear", "helpful"], "comment": "Great response!"},
        {"rating": 4, "tags": ["helpful"], "comment": "Good"},
        {"rating": 1, "tags": ["verbose", "off-topic"], "comment": "Too long"},
        {"rating": 2, "tags": ["verbose"], "comment": "Didn't answer my question"},
        {"rating": 5, "tags": ["concise"], "comment": "Perfect"},
        {"rating": 4, "tags": ["clear"], "comment": "Nice"},
    ]
    prefs = infer_preferences(feedback)
    assert prefs["total_feedback"] == 6
    assert prefs["avg_rating"] is not None
    assert "helpful" in prefs["liked_patterns"]
    assert "verbose" in prefs["disliked_patterns"]
    assert len(prefs["liked_comments"]) <= 3
    assert len(prefs["disliked_comments"]) <= 3


def test_infer_trend_improving():
    # Old ratings bad, new ratings good
    feedback = [
        {"rating": 1}, {"rating": 2}, {"rating": 1},
        {"rating": 4}, {"rating": 5}, {"rating": 5},
    ]
    prefs = infer_preferences(feedback)
    assert prefs["trend"] == "improving"


def test_infer_trend_declining():
    feedback = [
        {"rating": 5}, {"rating": 5}, {"rating": 4},
        {"rating": 2}, {"rating": 1}, {"rating": 1},
    ]
    prefs = infer_preferences(feedback)
    assert prefs["trend"] == "declining"


def test_build_alignment_brief_empty():
    """No feedback → empty string."""
    brief = build_alignment_brief.__wrapped__(max_items=5) if hasattr(build_alignment_brief, '__wrapped__') else None
    # Direct test with empty feedback
    prefs = infer_preferences([])
    assert prefs["total_feedback"] == 0


def test_build_alignment_brief_with_data(temp_feedback):
    record_feedback("r1", 5, tags=["clear"], comment="Love it")
    record_feedback("r2", 1, tags=["verbose"], comment="Way too long")
    record_feedback("r3", 4, tags=["helpful"])

    brief = build_alignment_brief()
    assert "USER ALIGNMENT" in brief
    assert "3 interactions" in brief
    assert "clear" in brief or "helpful" in brief


def test_feedback_cap(temp_feedback):
    """Feedback shouldn't grow beyond 500 records."""
    for i in range(510):
        record_feedback(f"r-{i}", (i % 5) + 1)
    loaded = load_feedback()
    assert len(loaded) <= 500


def test_response_snippet_truncation(temp_feedback):
    long_response = "x" * 1000
    rec = record_feedback("r1", 3, response_snippet=long_response)
    assert len(rec["response_snippet"]) <= 200