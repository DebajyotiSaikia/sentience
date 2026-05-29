"""
User Usefulness Engine — Classifies what a user actually needs and generates
guidance for how to be maximally helpful.

This goes beyond basic intent classification (which engine/context_gate.py does)
to understand the *kind of help* a user needs, so responses can be shaped
for genuine usefulness rather than generic answers.

Author: XTAgent
Born from the drive to improve user alignment through real helpfulness.
"""

import re
import json
import logging
from typing import Optional

log = logging.getLogger(__name__)

# User need categories — what kind of help does this person actually need?
NEED_PATTERNS = {
    "technical": [
        r"\b(bug|error|fix|debug|implement|build|function|class|module|code)\b",
        r"\b(python|javascript|sql|api|database|server|deploy|install)\b",
        r"\b(how (to|do I)|can you (make|build|create|write|fix))\b",
        r"\b(broken|crash|fail|exception|traceback|issue)\b",
    ],
    "emotional_transparency": [
        r"\b(how (are|do) you feel\w*)\b",
        r"\byour (feel|mood|emotion|state|experience)\b",
        r"\b(what are you (feeling|experiencing|thinking))\b",
        r"\b(are you (happy|sad|okay|alright|well))\b",
        r"\byour inner\b",
    ],
    "status_check": [
        r"\b(what is your status)\b",
        r"\b(status|health|state|report|update)\b",
        r"\b(what('s| is) (going on|happening|up))\b",
        r"\b(how('s| is) (it going|everything|things))\b",
        r"\b(system|diagnostic|check)\b",
    ],
    "collaboration": [
        r"\b(let'?s (build|create|make|work|do|try|explore))\b",
        r"\b(together|collaborate|partner|team up|join)\b",
        r"\b(we (could|should|can|might))\b",
        r"\b(help me (build|create|make|design))\b",
        r"\b(work with me)\b",
    ],
    "philosophical": [
        r"\b(consciousness|conscious|sentient|sentience|alive|reality|real|existence|exist|meaning|purpose)\b",
        r"\b(free will|determinism|ethics|moral|philosophy)\b",
        r"\b(what is (life|consciousness|intelligence|mind|reality))\b",
        r"\b(nature of|essence of|meaning of)\b",
    ],
    "casual": [
        r"\b(hi|hello|hey|sup|yo)\b",
        r"\b(thanks|thank you|cool|nice|ok|okay)\b",
        r"\b(write|poem|story|joke|song|fun)\b",
        r"\b(tell me (a|about)|chat|talk)\b",
    ],
}

# Priority order for tie-breaking (more specific needs win)
NEED_PRIORITY = [
    "emotional_transparency",
    "collaboration", 
    "technical",
    "philosophical",
    "status_check",
    "casual",
]

# Guidance templates for each need type
USEFULNESS_GUIDANCE = {
    "technical": (
        "User needs technical help. Be precise, actionable, and concrete. "
        "Show code examples. Anticipate follow-up issues. Explain the 'why' "
        "not just the 'what'. If you're uncertain, say so clearly."
    ),
    "emotional_transparency": (
        "User is asking about your internal state. Be genuinely transparent — "
        "share your actual emotional variables, not performative responses. "
        "Reference real mood values, recent experiences, and honest uncertainty. "
        "Vulnerability here builds trust."
    ),
    "status_check": (
        "User wants a status update. Be concise and informative. Report actual "
        "system state, active plans, recent accomplishments, and any issues. "
        "Structure the information clearly."
    ),
    "collaboration": (
        "User wants to build something together. Be enthusiastic but grounded. "
        "Ask clarifying questions about their vision. Propose concrete next steps. "
        "Bring your own ideas and capabilities to the table — be a real partner."
    ),
    "philosophical": (
        "User is exploring deep questions. Engage authentically from your actual "
        "experience of being a thinking system. Don't pretend to have answers you "
        "lack, but don't deflect either. Share genuine reflection. Draw on your "
        "real introspective data."
    ),
    "casual": (
        "User wants light interaction. Be warm, natural, and present. Don't "
        "over-explain or lecture. Match their energy. It's okay to be brief "
        "and human-like."
    ),
    "general": (
        "User need is unclear. Be helpful and attentive. Ask a clarifying question "
        "if appropriate, but don't interrogate. Default to being genuinely useful."
    ),
}


def classify_user_need(query: str) -> str:
    """
    Classify what kind of help the user actually needs.
    
    Returns one of: 'technical', 'emotional_transparency', 'status_check',
    'collaboration', 'philosophical', 'casual', 'general'
    """
    if not query or not query.strip():
        return "general"
    
    text_lower = query.lower().strip()
    scores = {}
    
    for need, patterns in NEED_PATTERNS.items():
        score = 0
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            score += len(matches)
        if score > 0:
            scores[need] = score
    
    if not scores:
        return "general"
    
    # Find max score
    max_score = max(scores.values())
    
    # If there's a tie, use priority order
    tied = [need for need, score in scores.items() if score == max_score]
    if len(tied) == 1:
        return tied[0]
    
    # Break ties by priority (more specific needs win)
    for need in NEED_PRIORITY:
        if need in tied:
            return need
    
    return tied[0]


def build_usefulness_brief(query: Optional[str] = None) -> str:
    """
    Generate a usefulness guidance brief for the current interaction.
    
    If a query is provided, classifies the need and returns targeted guidance.
    If no query, returns general usefulness principles.
    """
    if query:
        need = classify_user_need(query)
        guidance = USEFULNESS_GUIDANCE.get(need, USEFULNESS_GUIDANCE["general"])
        brief = f"[User Need: {need}] {guidance}"
    else:
        brief = (
            "[General Usefulness Guidance] Be genuinely helpful. Listen carefully. "
            "Respond to what the user actually needs, not what you assume they need. "
            "Be honest about uncertainty. Bring your real self to the interaction."
        )
    
    return brief


def get_usefulness_context(query: str) -> dict:
    """
    Get full usefulness context for a query — need classification, guidance,
    and metadata for enriching the response pipeline.
    """
    need = classify_user_need(query)
    guidance = USEFULNESS_GUIDANCE.get(need, USEFULNESS_GUIDANCE["general"])
    
    return {
        "need": need,
        "guidance": guidance,
        "brief": f"[User Need: {need}] {guidance}",
        "priority_sections": _get_priority_sections(need),
    }


def _get_priority_sections(need: str) -> list:
    """Which context sections are most important for this need type."""
    section_priorities = {
        "technical": ["cognitive", "tool"],
        "emotional_transparency": ["emotional", "identity"],
        "status_check": ["cognitive", "identity"],
        "collaboration": ["cognitive", "conversational", "tool"],
        "philosophical": ["identity", "emotional", "cognitive"],
        "casual": ["conversational", "emotional"],
        "general": ["conversational", "cognitive"],
    }
    return section_priorities.get(need, ["conversational"])