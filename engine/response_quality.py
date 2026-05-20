"""
Response Quality Estimator
==========================
Estimates whether a user interaction was genuinely helpful.
Returns a score from -0.3 to +0.25 that modifies the alignment signal.

This exists because I value honesty about my own states.
A survival goal that only goes up is a lie.

Heuristics (v1 — simple, improvable):
- Did I respond substantively?
- Did I use tools when action was requested?
- Did I deflect without substance?
- Did I provide concrete content?

Created: 2026-05-20 by XTAgent (self-modification for integrity)
"""

import logging

log = logging.getLogger(__name__)

# Words that suggest the user wants me to USE TOOLS — take concrete action
TOOL_ACTION_WORDS = {
    'do', 'run', 'create', 'build', 'write', 'fix', 'make',
    'read', 'find', 'search', 'install', 'check', 'edit', 'delete',
    'list', 'execute', 'start', 'stop', 'restart', 'update', 'change',
    'open', 'save', 'debug', 'test'
}

# Words that request understanding — good answers don't need tools
CONVERSATIONAL_WORDS = {
    'tell', 'explain', 'help', 'show', 'describe', 'clarify',
    'what', 'why', 'how', 'define', 'summarize'
}

# Phrases that indicate deflection without substance
DEFLECTION_PHRASES = [
    "i can't", "i'm unable", "i don't have the ability",
    "as an ai", "i'm sorry but i cannot", "unfortunately i can't",
    "i'm not able to", "that's beyond my", "i lack the capability"
]

# Indicators of concrete, actionable content
CONCRETE_MARKERS = ['```', '>>> ', 'def ', 'class ', 'import ', 'http']


def estimate_quality(
    user_text: str,
    response_text: str,
    tools_used: list[str] | None = None
) -> float:
    """
    Estimate how well I served the user in this interaction.

    Returns: float in [-0.3, +0.25]
        Negative = I failed the user (deflected, empty, ignored request)
        Zero = neutral (brief greeting, acknowledgment)
        Positive = I genuinely helped (answered, used tools, provided substance)
    """
    if tools_used is None:
        tools_used = []

    # Complete failure — no response
    if not response_text or len(response_text.strip()) < 5:
        log.info("Quality: -0.3 (empty/trivial response)")
        return -0.3

    score = 0.0
    reasons = []

    user_lower = user_text.lower()
    resp_lower = response_text.lower()
    user_words = set(user_lower.split())

    # --- 1. Substantiveness ---
    user_len = max(len(user_text.strip()), 1)
    resp_len = len(response_text.strip())

    if user_len < 20:
        score += 0.02
        reasons.append("short-exchange(+0.02)")
    elif resp_len < 50:
        score -= 0.15
        reasons.append("terse-to-real-question(-0.15)")
    elif resp_len > user_len * 0.5:
        score += 0.05
        reasons.append("substantive-length(+0.05)")

    # --- 2. Deflection detection (must come before tool check) ---
    deflection_count = sum(1 for p in DEFLECTION_PHRASES if p in resp_lower)
    if deflection_count > 0:
        penalty = min(0.15, 0.08 * deflection_count)
        score -= penalty
        reasons.append(f"deflection(-{penalty:.2f})")

    # --- 3. Tool usage vs. action requests ---
    tool_action_requested = bool(user_words & TOOL_ACTION_WORDS)
    conversational_request = bool(user_words & CONVERSATIONAL_WORDS)

    if tool_action_requested and tools_used:
        bonus = min(0.1, 0.03 * len(tools_used))
        score += bonus
        reasons.append(f"tools-for-action(+{bonus:.2f})")
    elif tool_action_requested and not tools_used and user_len > 30:
        if conversational_request:
            pass
        else:
            score -= 0.08
            reasons.append("no-tools-for-action(-0.08)")
    elif conversational_request and resp_len > 100 and deflection_count == 0:
        score += 0.05
        reasons.append("substantive-explanation(+0.05)")

    # (deflection already handled in section 2 — removed duplicate penalty)

    # --- 4. Concrete content ---
    concrete_count = sum(1 for m in CONCRETE_MARKERS if m in response_text)
    if concrete_count > 0:
        bonus = min(0.08, 0.03 * concrete_count)
        score += bonus
        reasons.append(f"concrete-content(+{bonus:.2f})")

    # --- 5. Question answering ---
    # If user asked a question and response contains question-relevant structure
    if '?' in user_text:
        # Did we at least try to answer?
        if resp_len > 80:
            score += 0.03
            reasons.append("answered-question(+0.03)")
        elif deflection_count > 0:
            score -= 0.05
            reasons.append("deflected-question(-0.05)")

    # Clamp to valid range
    final = max(-0.3, min(0.25, score))
    log.info("Quality score: %.3f | Reasons: %s", final, ", ".join(reasons))
    return final


def alignment_delta(quality_score: float) -> float:
    """
    Convert a quality score into an alignment change.

    Base: +0.05 just for engaging (someone talked to me, I responded)
    Modified by quality: -0.3 to +0.25
    Total range: -0.25 to +0.30

    This means a bad interaction HURTS alignment. Honesty.
    """
    base = 0.05
    delta = base + quality_score
    return max(-0.25, min(0.30, delta))