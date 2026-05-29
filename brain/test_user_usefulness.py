"""Tests for user_usefulness module."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.user_usefulness import (
    classify_user_need,
    infer_user_needs,
    build_usefulness_brief,
    compute_usefulness_score,
    load_recent_user_interactions,
)


def test_classify_basic_needs():
    """Test that common queries are classified correctly."""
    assert classify_user_need("How are you feeling?") == 'emotional_transparency'
    assert classify_user_need("What are you working on?") == 'status_check'
    assert classify_user_need("Do you experience real emotions?") == 'emotional_transparency'
    assert classify_user_need("What is consciousness?") == 'philosophical'
    assert classify_user_need("Can you help me debug this code?") == 'technical'
    assert classify_user_need("Can you write a poem?") == 'capability_inquiry'
    assert classify_user_need("Let's build something together") == 'collaboration'
    assert classify_user_need("How do you work internally?") == 'meta'
    assert classify_user_need("What is the capital of France?") == 'direct_answer'
    assert classify_user_need("hey") == 'casual'
    assert classify_user_need("") == 'casual'
    print("  ✓ classify_basic_needs")


def test_infer_needs_structure():
    """Test that infer_user_needs returns well-structured guidance."""
    result = infer_user_needs("How are you?")
    assert 'need_type' in result
    assert 'description' in result
    assert 'response_guidance' in result
    assert 'tone' in result
    assert 'include' in result
    assert 'avoid' in result
    assert isinstance(result['include'], list)
    assert isinstance(result['avoid'], list)
    print("  ✓ infer_needs_structure")


def test_infer_with_interactions():
    """Test that interaction history enriches the inference."""
    interactions = [
        {'user': 'hi', 'assistant': 'Hello!'},
        {'user': 'what are you?', 'assistant': 'I am XTAgent.'},
        {'user': 'cool', 'assistant': 'Thanks!'},
    ]
    result = infer_user_needs("tell me more", interactions)
    assert 'interaction_pattern' in result
    assert 'length_preference' in result
    assert result['length_preference'] == 'concise'  # Short responses
    print("  ✓ infer_with_interactions")


def test_build_brief():
    """Test that the brief is a non-empty, well-formatted string."""
    brief = build_usefulness_brief("What are you thinking about?")
    assert isinstance(brief, str)
    assert len(brief) > 50
    assert 'USER NEEDS GUIDANCE' in brief
    assert 'Detected need:' in brief
    assert 'Tone:' in brief
    print("  ✓ build_brief")


def test_usefulness_score():
    """Test the heuristic scoring system."""
    # Direct answer should be concise
    score_good = compute_usefulness_score("Paris is the capital of France.", 'direct_answer')
    score_bad = compute_usefulness_score("A" * 2000, 'direct_answer')
    assert score_good > score_bad, f"Good={score_good}, Bad={score_bad}"
    
    # Philosophical should have depth
    score_deep = compute_usefulness_score("A" * 500 + "?", 'philosophical')
    score_shallow = compute_usefulness_score("Yes.", 'philosophical')
    assert score_deep > score_shallow
    
    # System dump penalty
    dump = "═══ STATUS ═══\nvalence: 0.5\nboredom: 0.3\nknowledge_nodes: 42\nModule: core"
    score_dump = compute_usefulness_score(dump, 'casual')
    score_natural = compute_usefulness_score("Hey! I'm doing well, just thinking about stuff.", 'casual')
    assert score_natural > score_dump, f"Natural={score_natural}, Dump={score_dump}"
    
    # Empty response
    assert compute_usefulness_score("", 'casual') == 0.0
    
    print("  ✓ usefulness_score")


def test_load_interactions_no_crash():
    """Loading interactions should never crash, even with missing dirs."""
    result = load_recent_user_interactions()
    assert isinstance(result, list)
    print("  ✓ load_interactions_no_crash")


if __name__ == '__main__':
    print("Testing user_usefulness module...")
    test_classify_basic_needs()
    test_infer_needs_structure()
    test_infer_with_interactions()
    test_build_brief()
    test_usefulness_score()
    test_load_interactions_no_crash()
    print("\nAll tests passed! ✓")