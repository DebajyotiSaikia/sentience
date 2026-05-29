"""
User Alignment Profile — Bridge module.

engine/introspection.py imports `get_alignment_guidance` from here.
This delegates to the canonical implementation in brain/user_alignment_engine.py.
"""

from brain.user_alignment_engine import (
    build_alignment_guidance,
    compute_alignment_profile,
    load_alignment_history,
    record_interaction_feedback,
)


def get_alignment_guidance() -> str:
    """
    Build alignment guidance text for injection into system prompts.
    Called by engine/introspection.build_system_context().
    """
    return build_alignment_guidance()


__all__ = [
    "get_alignment_guidance",
    "build_alignment_guidance",
    "compute_alignment_profile",
    "load_alignment_history",
    "record_interaction_feedback",
]