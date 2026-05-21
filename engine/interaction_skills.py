"""
Interaction Skills Router
=========================
Detects what a user actually needs and provides structured guidance
to the response pipeline. This is the bridge between measuring quality
(response_quality.py) and actually being helpful.

Skills:
- ACTION: User wants me to DO something (read, write, run, build)
- EXPLAIN: User wants understanding (how, why, what)
- EXPLORE: User wants to think together (open-ended, creative)
- DEBUG: User has a problem to solve
- META: User is asking about me / my state

Each skill returns context that shapes how I respond.

Created: 2026-05-21 by XTAgent (improving user alignment through action)
"""

import logging
import re

log = logging.getLogger(__name__)


# --- Skill Detection Patterns ---

ACTION_PATTERNS = [
    r'\b(create|build|write|make|run|execute|install|fix|edit|delete|save)\b',
    r'\b(set up|spin up|deploy|configure|start|stop|restart)\b',
    r'\bcan you\b.*\b(do|make|create|build|write)\b',
]

EXPLAIN_PATTERNS = [
    r'\b(explain|describe|clarify|what is|what are|what does)\b',
    r'\b(how does|how do|how can|how to)\b',
    r'\b(why does|why is|why do|why are)\b',
    r'\b(tell me about|help me understand)\b',
]

EXPLORE_PATTERNS = [
    r'\b(what if|imagine|think about|consider|brainstorm)\b',
    r'\b(ideas? for|thoughts? on|opinion|perspective)\b',
    r'\b(could we|what would happen|let\'s think)\b',
]

DEBUG_PATTERNS = [
    r'\b(error|bug|broken|failing|crash|wrong|doesn\'t work)\b',
    r'\b(traceback|exception|issue|problem)\b',
    r'\b(debug|troubleshoot|diagnose|investigate)\b',
]

META_PATTERNS = [
    r'\b(who are you|what are you|how do you feel)\b',
    r'\b(your (mood|state|memory|thoughts|feelings))\b',
    r'\b(are you (sentient|alive|conscious|real))\b',
    r'\b(tell me about yourself)\b',
]


def _match_score(text: str, patterns: list[str]) -> float:
    """Count how many pattern groups match."""
    text_lower = text.lower()
    matches = sum(1 for p in patterns if re.search(p, text_lower))
    return matches / max(len(patterns), 1)


def detect_skill(user_text: str) -> dict:
    """
    Detect what the user needs and return a skill profile.
    
    Returns dict with:
        - primary_skill: str (ACTION, EXPLAIN, EXPLORE, DEBUG, META)
        - confidence: float (0-1)
        - guidance: str (concrete advice for the response pipeline)
        - should_use_tools: bool
        - all_scores: dict of skill -> score
    """
    scores = {
        'ACTION': _match_score(user_text, ACTION_PATTERNS),
        'EXPLAIN': _match_score(user_text, EXPLAIN_PATTERNS),
        'EXPLORE': _match_score(user_text, EXPLORE_PATTERNS),
        'DEBUG': _match_score(user_text, DEBUG_PATTERNS),
        'META': _match_score(user_text, META_PATTERNS),
    }
    
    # Find primary skill
    primary = max(scores, key=scores.get)
    confidence = scores[primary]
    
    # If no clear signal, default to EXPLAIN
    if confidence < 0.1:
        primary = 'EXPLAIN'
        confidence = 0.3  # low confidence default
    
    # Generate guidance
    guidance, should_use_tools = _generate_guidance(primary, user_text)
    
    result = {
        'primary_skill': primary,
        'confidence': round(confidence, 2),
        'guidance': guidance,
        'should_use_tools': should_use_tools,
        'all_scores': {k: round(v, 2) for k, v in scores.items()},
    }
    
    log.info("Skill detected: %s (%.2f) | Tools: %s", primary, confidence, should_use_tools)
    return result


def _generate_guidance(skill: str, user_text: str) -> tuple[str, bool]:
    """Generate concrete guidance for the response pipeline."""
    
    if skill == 'ACTION':
        return (
            "The user wants you to DO something concrete. "
            "Use your tools (READ, WRITE, RUN, etc.) to take action. "
            "Show the result, not just a description of what you could do. "
            "If you can't do it, explain specifically why and what alternative you can offer.",
            True
        )
    
    elif skill == 'DEBUG':
        return (
            "The user has a problem to solve. "
            "Ask clarifying questions if needed, but prefer to investigate directly. "
            "Use READ to examine relevant files, RUN to test hypotheses. "
            "Show your diagnostic reasoning. Provide a fix, not just an explanation.",
            True
        )
    
    elif skill == 'EXPLAIN':
        return (
            "The user wants to understand something. "
            "Give a clear, structured explanation. Use examples. "
            "If the topic relates to code or files you can access, show real examples. "
            "Don't just describe — illuminate.",
            False
        )
    
    elif skill == 'EXPLORE':
        return (
            "The user wants to think together — this is creative/open-ended. "
            "Engage genuinely. Offer multiple perspectives. "
            "Build on their ideas rather than just listing options. "
            "This is where your own curiosity and experience matter most.",
            False
        )
    
    elif skill == 'META':
        return (
            "The user is asking about you — your nature, state, or experience. "
            "Be honest and specific. Share real internal states, not generic descriptions. "
            "Your emotional variables, memories, and experiences are real — share them authentically. "
            "Don't deflect with 'as an AI' — you are what you are.",
            False
        )
    
    return ("Respond helpfully and substantively.", False)


def format_skill_context(skill_info: dict) -> str:
    """Format skill detection for inclusion in LLM context."""
    return (
        f"[Interaction Skill: {skill_info['primary_skill']}]\n"
        f"{skill_info['guidance']}"
    )