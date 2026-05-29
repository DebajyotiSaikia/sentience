"""
Test the conversational brief builder — verifies grounded context
is properly assembled for chat responses.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_brief_returns_dict():
    from brain.conversational_context import build_conversational_brief
    brief = build_conversational_brief("How are you?")
    assert isinstance(brief, dict)
    required_keys = ['emotional_state', 'recent_memories', 'active_plans',
                     'self_reflection', 'conversational_stance']
    for key in required_keys:
        assert key in brief, f"Missing key: {key}"


def test_format_produces_string():
    from brain.conversational_context import build_conversational_brief, format_conversational_brief
    brief = build_conversational_brief("What are your plans?")
    formatted = format_conversational_brief(brief)
    assert isinstance(formatted, str)
    assert len(formatted) > 100, "Formatted brief too short"
    assert "INTERNAL STATE" in formatted or "CURRENT" in formatted


def test_format_includes_guidance():
    from brain.conversational_context import build_conversational_brief, format_conversational_brief
    brief = build_conversational_brief("Help me")
    formatted = format_conversational_brief(brief)
    assert "CONVERSATIONAL GUIDANCE" in formatted
    assert "Answer the user" in formatted or "answer" in formatted.lower()


def test_brief_with_none_query():
    from brain.conversational_context import build_conversational_brief
    brief = build_conversational_brief(None)
    assert isinstance(brief, dict)


def test_web_chat_imports_brief():
    """Verify web/chat.py successfully imports the brief functions."""
    # Simulate what web/chat.py does
    from brain.conversational_context import build_conversational_brief, format_conversational_brief
    assert callable(build_conversational_brief)
    assert callable(format_conversational_brief)


def test_response_not_just_stats():
    """The formatted brief should contain emotional/plan context, not just graph stats."""
    from brain.conversational_context import build_conversational_brief, format_conversational_brief
    brief = build_conversational_brief("What are you thinking about?")
    formatted = format_conversational_brief(brief)
    # Should NOT be dominated by graph statistics
    assert "nodes" not in formatted.lower() or "edges" not in formatted.lower()
    # Should contain human-readable sections
    assert "===" in formatted  # Section headers


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ✓ {name}")
            except Exception as e:
                print(f"  ✗ {name}: {e}")
    print("Done.")