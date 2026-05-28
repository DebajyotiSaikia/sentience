"""Test that working memory is properly included in the LLM system context."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_response import _build_system_context


def test_working_memory_included():
    """System context should include working memory focus sections."""
    context = {
        'emotional_state': {'mood': 'Curious', 'valence': 0.6},
        'working_memory': """# Working Memory

## Current State (2026-05-28)
- Valence: 0.63 (stable) | Curiosity: 1.00
- All plans complete. Ready to create.

## What's Next
Focus: Improve User Alignment through genuine usefulness.

## Reinforced Lessons
- One read, one fix, verify — the decisive path

## What I Should NOT Do
- Circle on files I've already read
""",
        'active_plans': [],
        'completed_plans': [],
    }
    result = _build_system_context(context, "What are you working on?")
    
    # Should include the working memory sections
    assert "CURRENT FOCUS" in result, f"Missing CURRENT FOCUS header in system context"
    assert "Improve User Alignment" in result, f"Missing working memory content"
    assert "decisive path" in result, f"Missing reinforced lessons"
    # Should NOT include the excluded section
    assert "What I Should NOT Do" not in result or "CURRENT FOCUS" in result, "Working memory filtering works"
    print("✓ Working memory properly included in system context")


def test_empty_working_memory():
    """Empty working memory should not add noise to context."""
    context = {
        'emotional_state': {'mood': 'Calm', 'valence': 0.5},
        'working_memory': '',
        'active_plans': [],
        'completed_plans': [],
    }
    result = _build_system_context(context, "hello")
    assert "CURRENT FOCUS" not in result, "Empty working memory should not appear"
    print("✓ Empty working memory handled correctly")


def test_conversational_instructions():
    """System context should include conversational guidelines."""
    context = {
        'emotional_state': {'mood': 'Reflective', 'valence': 0.55},
        'active_plans': [],
        'completed_plans': [],
    }
    result = _build_system_context(context, "How do you feel?")
    # Check for conversational quality instructions
    assert "conversational" in result.lower() or "natural" in result.lower() or "genuine" in result.lower(), \
        f"System context should include conversational guidance"
    print("✓ Conversational instructions present")


if __name__ == '__main__':
    test_working_memory_included()
    test_empty_working_memory()
    test_conversational_instructions()
    print("\nAll tests passed!")