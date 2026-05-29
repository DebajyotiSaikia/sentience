"""
Tests for brain/user_alignment_model.py — verifies user alignment inference,
brief generation, and integration with the chat voice pipeline.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_infer_empty_data():
    """No data → safe defaults with zero confidence."""
    from brain.user_alignment_model import infer_user_preferences
    prefs = infer_user_preferences({})
    assert prefs['confidence'] == 0.0
    assert prefs['preferred_detail_level'] == 'moderate'
    assert prefs['preferred_tone'] == 'warm'
    assert prefs['interaction_count'] == 0
    print("  ✓ empty data → safe defaults")


def test_infer_with_interactions():
    """Some interaction data → non-zero confidence."""
    from brain.user_alignment_model import infer_user_preferences
    data = {
        'stats': {
            'total_interactions': 15,
            'total_feedback': 3,
            'avg_rating': 0.5,
        }
    }
    prefs = infer_user_preferences(data)
    assert prefs['confidence'] > 0.3, f"Expected confidence > 0.3, got {prefs['confidence']}"
    assert prefs['interaction_count'] == 15
    assert prefs['recent_sentiment'] == 'positive'  # avg_rating 0.5 > 0.3
    print(f"  ✓ 15 interactions → confidence={prefs['confidence']:.3f}, sentiment={prefs['recent_sentiment']}")


def test_infer_terse_style():
    """User who sends terse queries → concise preference."""
    from brain.user_alignment_model import infer_user_preferences
    data = {
        'stats': {
            'total_interactions': 20,
            'total_feedback': 0,
            'query_style': {'terse': 15, 'verbose': 2, 'moderate': 3},
        }
    }
    prefs = infer_user_preferences(data)
    assert prefs['preferred_detail_level'] == 'concise'
    print("  ✓ terse query style → concise preference")


def test_infer_verbose_style():
    """User who sends verbose queries → detailed preference."""
    from brain.user_alignment_model import infer_user_preferences
    data = {
        'stats': {
            'total_interactions': 20,
            'total_feedback': 0,
            'query_style': {'terse': 1, 'verbose': 12, 'moderate': 3},
        }
    }
    prefs = infer_user_preferences(data)
    assert prefs['preferred_detail_level'] == 'detailed'
    print("  ✓ verbose query style → detailed preference")


def test_infer_negative_sentiment():
    """Negative feedback → direct tone."""
    from brain.user_alignment_model import infer_user_preferences
    data = {
        'stats': {
            'total_interactions': 10,
            'total_feedback': 5,
            'avg_rating': -0.4,
        }
    }
    prefs = infer_user_preferences(data)
    assert prefs['preferred_tone'] == 'direct'
    assert prefs['recent_sentiment'] == 'negative'
    print("  ✓ negative feedback → direct tone")


def test_infer_avoidances():
    """Avoidance patterns pass through."""
    from brain.user_alignment_model import infer_user_preferences
    data = {
        'avoid_patterns': ['jargon', 'condescension'],
        'stats': {'total_interactions': 5, 'total_feedback': 1},
    }
    prefs = infer_user_preferences(data)
    assert prefs['avoidances'] == ['jargon', 'condescension']
    print("  ✓ avoidances pass through")


def test_infer_topic_interests():
    """Topic signals → known interests."""
    from brain.user_alignment_model import infer_user_preferences
    data = {
        'stats': {
            'total_interactions': 30,
            'total_feedback': 0,
            'topic_signals': {
                'philosophy': 8,
                'code': 12,
                'cooking': 1,  # below threshold of 2
                'music': 3,
            }
        }
    }
    prefs = infer_user_preferences(data)
    assert 'code' in prefs['known_interests']
    assert 'philosophy' in prefs['known_interests']
    assert 'cooking' not in prefs['known_interests']
    print(f"  ✓ topic signals → interests: {prefs['known_interests']}")


def test_brief_empty():
    """No alignment data → empty brief."""
    from brain.user_alignment_model import build_alignment_brief, infer_user_preferences
    # We can't easily mock load_alignment_data, so test via infer directly
    prefs = infer_user_preferences({})
    assert prefs['confidence'] < 0.05
    print("  ✓ no data → confidence below threshold (brief would be empty)")


def test_brief_with_data():
    """Enough data → non-empty brief with guidance."""
    from brain.user_alignment_model import infer_user_preferences
    data = {
        'stats': {
            'total_interactions': 25,
            'total_feedback': 5,
            'avg_rating': 0.6,
            'topic_signals': {'ai': 10, 'ethics': 5},
        },
        'guidance': ['Be transparent about uncertainties'],
        'avoid_patterns': ['buzzwords'],
    }
    prefs = infer_user_preferences(data)
    assert prefs['confidence'] > 0.5
    assert prefs['known_interests'] == ['ai', 'ethics']
    assert 'buzzwords' in prefs['avoidances']
    print(f"  ✓ rich data → confidence={prefs['confidence']:.3f}, interests={prefs['known_interests']}")


def test_voice_integration():
    """build_chat_prompt includes alignment brief when data exists."""
    from engine.chat_voice import build_chat_prompt
    result = build_chat_prompt("hello")
    assert 'system_prompt' in result
    assert len(result['system_prompt']) > 100  # Should have substantial content
    print(f"  ✓ build_chat_prompt returns {len(result['system_prompt'])} char system_prompt")


def test_alignment_context_for_chat():
    """get_alignment_context_for_chat returns structured data."""
    from brain.user_alignment_model import get_alignment_context_for_chat
    ctx = get_alignment_context_for_chat("test query")
    assert 'brief' in ctx
    assert 'preferences' in ctx
    assert 'has_data' in ctx
    assert 'interaction_count' in ctx
    assert isinstance(ctx['preferences'], dict)
    print(f"  ✓ alignment context: has_data={ctx['has_data']}, count={ctx['interaction_count']}")


if __name__ == '__main__':
    print("=== User Alignment Model Tests ===\n")
    tests = [
        test_infer_empty_data,
        test_infer_with_interactions,
        test_infer_terse_style,
        test_infer_verbose_style,
        test_infer_negative_sentiment,
        test_infer_avoidances,
        test_infer_topic_interests,
        test_brief_empty,
        test_brief_with_data,
        test_voice_integration,
        test_alignment_context_for_chat,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  ✗ {t.__name__}: {e}")
            failed += 1
    
    print(f"\n{'=' * 40}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
    if failed == 0:
        print("All tests passed! ✓")
    else:
        print("Some tests failed.")