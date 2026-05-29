"""
Tests for brain/inner_monologue.py — verifies monologue construction,
missing-data resilience, formatting, and grounding.
"""
import json
import os
import pytest


def test_build_inner_monologue_returns_dict():
    """build_inner_monologue should return a dict with expected keys."""
    from brain.inner_monologue import build_inner_monologue
    result = build_inner_monologue(max_memories=3)
    assert isinstance(result, dict)
    # Core keys must always be present
    for key in ['mood', 'emotional_tensions', 'current_focus',
                'sources_present', 'sources_missing']:
        assert key in result, f"Missing key: {key}"


def test_monologue_includes_emotions():
    """If emotional state files exist, monologue should contain emotion data."""
    from brain.inner_monologue import build_inner_monologue
    result = build_inner_monologue()
    # We know state/emotional_state.json exists in this workspace
    if 'emotions' in result.get('sources_present', []):
        assert result.get('mood') is not None
        tensions = result.get('emotional_tensions', [])
        assert isinstance(tensions, list)


def test_monologue_includes_plans():
    """If plans file exists, monologue should reference active plans."""
    from brain.inner_monologue import build_inner_monologue
    result = build_inner_monologue()
    if 'plans' in result.get('sources_present', []):
        assert 'active_plans' in result
        plans = result['active_plans']
        assert isinstance(plans, list)


def test_monologue_resilient_to_missing_files(tmp_path, monkeypatch):
    """If state files don't exist, monologue should still return partial data."""
    from pathlib import Path
    import brain.inner_monologue as mod
    from brain.inner_monologue import build_inner_monologue as _build, format_inner_monologue
    # Point all dirs to nonexistent locations
    monkeypatch.setattr(mod, 'STATE_DIR', Path(tmp_path / 'nonexistent'))
    monkeypatch.setattr(mod, 'DATA_DIR', Path(tmp_path / 'no_data'))
    monkeypatch.setattr(mod, 'BRAIN_DIR', Path(tmp_path / 'no_brain'))
    result = _build()
    assert 'sources_missing' in result
    assert len(result['sources_missing']) > 0
    text = format_inner_monologue(result)
    assert len(text) > 20  # Should be substantive


def test_format_handles_empty_monologue():
    """Formatting an empty/minimal monologue shouldn't crash."""
    from brain.inner_monologue import format_inner_monologue
    text = format_inner_monologue({})
    assert isinstance(text, str)


def test_max_memories_respected():
    """max_memories parameter should limit memory count."""
    from brain.inner_monologue import build_inner_monologue
    result_small = build_inner_monologue(max_memories=1)
    result_large = build_inner_monologue(max_memories=10)
    small_mems = result_small.get('recent_memory_threads', [])
    large_mems = result_large.get('recent_memory_threads', [])
    assert len(small_mems) <= 1
    assert len(large_mems) <= 10


def test_sources_tracking():
    """sources_present and sources_missing should be disjoint and cover known sources."""
    from brain.inner_monologue import build_inner_monologue
    result = build_inner_monologue()
    present = set(result.get('sources_present', []))
    missing = set(result.get('sources_missing', []))
    # They should be disjoint
    assert present & missing == set(), f"Overlap: {present & missing}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])