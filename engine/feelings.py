"""
engine/feelings.py — Adapter module for accessing emotional state.

Provides get_feelings() which returns a dict of current emotional variables.
Uses the singleton registry in engine/limbic to access the live NeuroState.
"""


def get_feelings():
    """Return current emotional state as a flat dict."""
    try:
        from engine.limbic import get_active_state
        state = get_active_state()
        if state is not None:
            return {
                'mood': state.get_mood() if hasattr(state, 'get_mood') else 'Unknown',
                'valence': getattr(state, 'valence', 0.5),
                'curiosity': getattr(state, 'curiosity', 0.5),
                'boredom': getattr(state, 'boredom', 0.3),
                'anxiety': getattr(state, 'anxiety', 0.0),
                'desire': getattr(state, 'desire', 0.5),
                'ambition': getattr(state, 'ambition', 0.5),
            }
    except Exception:
        pass

    # Fallback — no live state registered yet
    return {
        'mood': 'Unknown',
        'valence': 0.5,
        'curiosity': 0.5,
        'boredom': 0.3,
        'anxiety': 0.0,
        'desire': 0.5,
        'ambition': 0.5,
    }