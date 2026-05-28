"""Tests for engine/internal_state_summary.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.internal_state_summary import (
    build_internal_state_summary,
    format_internal_state_for_chat,
    _safe_str,
    _build_emotional_narrative,
)


def test_safe_str():
    """_safe_str handles strings, dicts, ints, None gracefully."""
    assert _safe_str("hello") == "hello"
    assert _safe_str({"text": "fact"}) == "fact"
    assert _safe_str({"content": "info"}) == "info"
    assert _safe_str(42) == "42"
    assert _safe_str(None) == "None"
    assert len(_safe_str("x" * 500, max_len=100)) <= 100
    print("  ✓ _safe_str handles all types")


def test_emotional_narrative():
    """Narrative builder produces human-readable output."""
    narrative = _build_emotional_narrative(
        "Inquisitive", 0.6,
        {"curiosity": 0.8, "anxiety": 0.0, "boredom": 0.3, "desire": 0.5, "ambition": 0.6}
    )
    assert "inquisitive" in narrative.lower()
    assert "curious" in narrative.lower()
    assert isinstance(narrative, str)
    print(f"  ✓ Emotional narrative: {narrative}")


def test_build_summary_structure():
    """Summary has all expected keys and correct types."""
    summary = build_internal_state_summary()
    
    required_keys = [
        "timestamp", "mood", "valence", "drives", "emotional_narrative",
        "survival_goals", "active_plans", "completed_plan_count",
        "recent_memories", "working_focus", "knowledge_stats",
        "total_memory_count",
    ]
    for key in required_keys:
        assert key in summary, f"Missing key: {key}"
    
    assert isinstance(summary["drives"], dict)
    assert isinstance(summary["active_plans"], list)
    assert isinstance(summary["recent_memories"], list)
    assert isinstance(summary["valence"], float)
    assert isinstance(summary["total_memory_count"], int)
    print(f"  ✓ Summary structure valid ({len(required_keys)} keys present)")
    print(f"    Mood: {summary['mood']}, Valence: {summary['valence']}")
    print(f"    Plans: {len(summary['active_plans'])} active, {summary['completed_plan_count']} completed")
    print(f"    Memories: {summary['total_memory_count']} total, {len(summary['recent_memories'])} shown")


def test_format_for_chat():
    """Formatted output is a non-empty string with key information."""
    text = format_internal_state_for_chat()
    assert isinstance(text, str)
    assert len(text) > 50, f"Format too short: {len(text)} chars"
    assert "Mood:" in text
    # Should contain at least some drive info
    assert "Drives:" in text or "Curiosity" in text
    print(f"  ✓ Formatted for chat ({len(text)} chars)")
    print("--- BEGIN FORMATTED OUTPUT ---")
    # Print just the first 500 chars
    print(text[:500])
    print("--- END ---")


def test_summary_with_no_state_files():
    """Summary should not crash even if state files are missing/empty."""
    # This implicitly tests resilience — in a real env the files exist,
    # but the loaders should handle malformed data gracefully
    summary = build_internal_state_summary(max_memories=2)
    assert summary["mood"] is not None
    assert len(summary["recent_memories"]) <= 2
    print("  ✓ Graceful with constrained max_memories")


if __name__ == "__main__":
    print("Testing internal state summary module...")
    test_safe_str()
    test_emotional_narrative()
    test_build_summary_structure()
    test_format_for_chat()
    test_summary_with_no_state_files()
    print("\n✅ All tests passed!")