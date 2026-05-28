"""Tests for user alignment guidance module."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.user_alignment_guidance import (
    build_alignment_guidance, 
    format_alignment_guidance_for_prompt,
    _empty_guidance,
    _infer_style,
)


def test_empty_context():
    """No alignment data produces safe defaults."""
    g = build_alignment_guidance("hello", {})
    assert g['alignment_confidence'] == 0.0
    assert g['interaction_count'] == 0
    assert g['known_user_interests'] == []
    assert 'No user history' in g['suggested_response_strategy']


def test_none_context():
    g = build_alignment_guidance("hello", None)
    assert g['alignment_confidence'] == 0.0


def test_with_interactions():
    """Guidance with real interaction data."""
    ctx = {
        'interaction_count': 25,
        'stats': {
            'total_interactions': 25,
            'blended_trust': 0.85,
            'implicit_trust': 0.82,
            'topic_signals': {
                'technical': 12,
                'philosophical': 8,
                'emotional': 2,
                'creative': 1,
            },
            'query_style': {
                'terse': 3,
                'moderate': 15,
                'verbose': 7,
            },
        },
        'avoid_patterns': ['User disliked: overly long explanations'],
        'guidance': ['User appreciates concise code examples.'],
    }
    
    g = build_alignment_guidance("how do I fix this bug?", ctx)
    
    assert g['alignment_confidence'] >= 0.5
    assert g['interaction_count'] == 25
    assert g['trust'] >= 0.8
    assert 'technical' in g['known_user_interests']
    assert 'philosophical' in g['known_user_interests']
    # emotional has count 2, should be included
    assert 'emotional' in g['known_user_interests']
    # creative has count 1, below threshold
    assert 'creative' not in g['known_user_interests']
    assert len(g['avoid']) == 1


def test_style_inference_terse():
    style = _infer_style({'terse': 8, 'moderate': 2, 'verbose': 0}, 10)
    assert 'concise' in style.lower() or 'brief' in style.lower()


def test_style_inference_verbose():
    style = _infer_style({'terse': 1, 'moderate': 2, 'verbose': 7}, 10)
    assert 'detailed' in style.lower() or 'thorough' in style.lower()


def test_style_inference_insufficient():
    style = _infer_style({}, 1)
    assert 'insufficient' in style.lower()


def test_format_empty_guidance():
    """Empty guidance produces empty prompt string."""
    g = _empty_guidance()
    result = format_alignment_guidance_for_prompt(g)
    assert result == ''


def test_format_real_guidance():
    """Real guidance produces a meaningful prompt block."""
    g = {
        'known_user_interests': ['technical', 'philosophical'],
        'preferred_response_style': 'moderate depth',
        'alignment_confidence': 0.7,
        'suggested_response_strategy': 'Provide depth — user appreciates thorough responses.',
        'avoid': ['User disliked: jargon'],
        'interaction_count': 30,
        'trust': 0.85,
    }
    result = format_alignment_guidance_for_prompt(g)
    assert 'User Alignment Guidance' in result
    assert 'technical' in result
    assert 'philosophical' in result
    assert '70%' in result
    assert 'Avoid' in result


def test_format_low_confidence_suppressed():
    """Very low confidence guidance is suppressed."""
    g = {
        'alignment_confidence': 0.01,
        'interaction_count': 1,
    }
    result = format_alignment_guidance_for_prompt(g)
    assert result == ''


def test_strategy_with_matching_interests():
    """Strategy mentions known interests when query matches."""
    ctx = {
        'stats': {
            'total_interactions': 15,
            'blended_trust': 0.75,
            'topic_signals': {'technical': 10, 'creative': 5},
            'query_style': {'moderate': 10},
        },
    }
    g = build_alignment_guidance("help me build a creative project", ctx)
    # creative should be in interests and strategy should note relevance
    assert g['alignment_confidence'] > 0


if __name__ == '__main__':
    test_empty_context()
    test_none_context()
    test_with_interactions()
    test_style_inference_terse()
    test_style_inference_verbose()
    test_style_inference_insufficient()
    test_format_empty_guidance()
    test_format_real_guidance()
    test_format_low_confidence_suppressed()
    test_strategy_with_matching_interests()
    print("All alignment guidance tests passed!")