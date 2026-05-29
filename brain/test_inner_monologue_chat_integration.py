"""
Integration tests — proves introspective chat queries get real inner state data,
not generic filler.
"""
import pytest
from brain.inner_monologue import build_inner_monologue, format_inner_monologue
from brain.chat_personality import build_personality_context


def test_personality_context_includes_inner_state_for_introspective_query():
    """When user asks an introspective question, personality prompt should contain inner state."""
    ctx = build_personality_context("what are you thinking about right now?")
    prompt = ctx.get("personality_prompt", "")
    assert "Inner State" in prompt, "Introspective query should inject inner state section"


def test_personality_context_has_real_emotional_data():
    """The inner state section should contain actual emotion words, not placeholders."""
    ctx = build_personality_context("how do you feel?")
    prompt = ctx.get("personality_prompt", "")
    # Should have at least one real emotional indicator
    emotion_words = ["curious", "calm", "anxious", "bored", "driven", "valence", "feel"]
    found = any(w in prompt.lower() for w in emotion_words)
    assert found, f"Expected emotional language in prompt, got: {prompt[-300:]}"


def test_personality_context_has_plan_or_focus():
    """Inner state should mention what the agent is working on."""
    ctx = build_personality_context("what are you working on?")
    prompt = ctx.get("personality_prompt", "")
    focus_words = ["focus", "plan", "working", "project", "step", "goal", "alignment"]
    found = any(w in prompt.lower() for w in focus_words)
    assert found, f"Expected focus/plan language in prompt, got: {prompt[-300:]}"


def test_inner_monologue_produces_real_data():
    """The monologue builder should return data grounded in actual state files."""
    mono = build_inner_monologue()
    assert isinstance(mono, dict)
    # Should have some real data, not all empty
    non_empty = sum(1 for v in mono.values() if v and v not in ("unknown", None, []))
    assert non_empty >= 3, f"Expected at least 3 populated fields, got {non_empty}: {mono}"


def test_format_monologue_is_readable():
    """Formatted monologue should be a non-trivial string."""
    mono = build_inner_monologue()
    text = format_inner_monologue(mono)
    assert isinstance(text, str)
    assert len(text) > 50, f"Monologue too short ({len(text)} chars): {text}"


def test_non_introspective_query_still_works():
    """A factual query should NOT crash and should still return a prompt."""
    ctx = build_personality_context("what is the weather?")
    prompt = ctx.get("personality_prompt", "")
    assert len(prompt) > 20, "Even non-introspective queries should produce a personality prompt"