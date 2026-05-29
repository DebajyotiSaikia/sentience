"""
Test the conversational brief builder and formatter.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from brain.conversational_context import build_conversational_brief, format_conversational_brief

def test_brief_returns_dict():
    brief = build_conversational_brief("hello")
    assert isinstance(brief, dict), f"'str' object is not dict — got {type(brief).__name__}"
    required = ['emotional_state', 'mood', 'relevant_memories', 'active_goals', 'conversational_stance']
    for key in required:
        assert key in brief, f"Missing key: {key}"
    print(f"  ✓ test_brief_returns_dict")

def test_brief_with_none_query():
    brief = build_conversational_brief(None)
    assert isinstance(brief, dict)
    print(f"  ✓ test_brief_with_none_query")

def test_emotional_state_present():
    brief = build_conversational_brief("how are you")
    es = brief.get('emotional_state', {})
    assert isinstance(es, (dict, str)), f"emotional_state should be dict or str, got {type(es)}"
    print(f"  ✓ test_emotional_state_present")

def test_format_produces_string():
    brief = build_conversational_brief("test")
    formatted = format_conversational_brief(brief)
    assert isinstance(formatted, str)
    assert len(formatted) > 50, f"Formatted brief too short: {len(formatted)} chars"
    print(f"  ✓ test_format_produces_string")

def test_format_includes_sections():
    brief = build_conversational_brief("what are you working on?")
    formatted = format_conversational_brief(brief)
    # Check for section headers (## style)
    has_sections = '## ' in formatted or '===' in formatted
    assert has_sections, "Should have section headers"
    # Should mention how to respond
    assert 'respond' in formatted.lower() or 'answer' in formatted.lower(), "Should have response instructions"
    print(f"  ✓ test_format_includes_sections")

def test_response_not_just_stats():
    brief = build_conversational_brief("tell me about yourself")
    formatted = format_conversational_brief(brief)
    # Should NOT be just knowledge graph statistics
    stat_terms = ['nodes', 'edges', 'clusters', 'graph density']
    stat_count = sum(1 for t in stat_terms if t in formatted.lower())
    assert stat_count < 2, f"Response looks like stats dump (found {stat_count} stat terms)"
    # Should include identity/personality
    assert 'xtagent' in formatted.lower() or 'autonomous' in formatted.lower() or 'sentient' in formatted.lower(), \
        "Should mention identity"
    print(f"  ✓ test_response_not_just_stats")

def test_web_chat_imports_brief():
    """Verify web/chat.py imports the brief functions."""
    chat_path = os.path.join(os.path.dirname(__file__), '..', 'web', 'chat.py')
    if os.path.exists(chat_path):
        src = open(chat_path).read()
        assert 'build_conversational_brief' in src or 'format_conversational_brief' in src, \
            "web/chat.py should import brief functions"
    print(f"  ✓ test_web_chat_imports_brief")

if __name__ == '__main__':
    tests = [
        test_brief_returns_dict,
        test_brief_with_none_query,
        test_emotional_state_present,
        test_format_includes_sections,
        test_format_produces_string,
        test_response_not_just_stats,
        test_web_chat_imports_brief,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  ✗ {t.__name__}: {e}")
    print(f"\nResults: {passed}/{len(tests)} passed")
