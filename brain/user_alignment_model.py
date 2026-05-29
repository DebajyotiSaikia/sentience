"""
User Alignment Model — Transforms raw alignment data into compact,
chat-usable guidance that shapes how I respond to users.

This bridges the gap between the data layer (engine/user_alignment.py)
and the prompt builder (engine/chat_voice.py). It answers: "What do I
know about this user, and how should that change my behavior?"
"""
import logging
from typing import Dict, Optional

log = logging.getLogger(__name__)


def load_alignment_data() -> dict:
    """Load raw alignment data from the persistence layer.
    
    Returns a normalized dict even if the file is missing or corrupt.
    """
    try:
        from engine.user_alignment import load_profile
        profile = load_profile()
        return profile.to_dict()
    except Exception as e:
        log.warning("Could not load alignment profile: %s", e)
        return {
            'feedback_history': [],
            'preferences': [],
            'avoid_patterns': [],
            'guidance': [],
            'stats': {},
        }


def infer_user_preferences(data: dict) -> dict:
    """Infer structured user preferences from raw alignment data.
    
    Returns a normalized preference dict with:
        preferred_detail_level: 'concise' | 'moderate' | 'detailed'
        preferred_tone: 'warm' | 'neutral' | 'direct'
        known_interests: list of topic strings the user gravitates toward
        avoidances: list of things the user dislikes
        recent_sentiment: 'positive' | 'neutral' | 'negative'
        interaction_count: int
        confidence: float 0.0-1.0 (how much data backs these inferences)
    """
    stats = data.get('stats', {})
    prefs = {
        'preferred_detail_level': 'moderate',
        'preferred_tone': 'warm',
        'known_interests': [],
        'avoidances': [],
        'recent_sentiment': 'neutral',
        'interaction_count': 0,
        'confidence': 0.0,
    }

    # --- Interaction volume ---
    n_interactions = stats.get('total_interactions', 0)
    n_feedback = stats.get('total_feedback', 0)
    prefs['interaction_count'] = n_interactions

    # Confidence scales with evidence
    if n_interactions == 0 and n_feedback == 0:
        return prefs  # No data — return defaults
    
    evidence = n_interactions + n_feedback * 3  # explicit feedback weighs more
    import math
    prefs['confidence'] = round(min(1.0, 1.0 - math.exp(-evidence / 30.0)), 3)

    # --- Detail level from query style ---
    query_style = stats.get('query_style', {})
    terse = query_style.get('terse', 0)
    verbose = query_style.get('verbose', 0)
    moderate = query_style.get('moderate', 0)
    total_style = terse + verbose + moderate
    if total_style >= 3:
        if terse > verbose * 2:
            prefs['preferred_detail_level'] = 'concise'
        elif verbose > terse * 2:
            prefs['preferred_detail_level'] = 'detailed'

    # --- Tone from feedback sentiment ---
    avg_rating = stats.get('avg_rating', 0.0)
    if n_feedback >= 2:
        if avg_rating > 0.3:
            prefs['recent_sentiment'] = 'positive'
            prefs['preferred_tone'] = 'warm'
        elif avg_rating < -0.2:
            prefs['recent_sentiment'] = 'negative'
            prefs['preferred_tone'] = 'direct'  # they want improvement, be crisp
    
    # --- Interests from topic signals ---
    topic_signals = stats.get('topic_signals', {})
    if topic_signals:
        sorted_topics = sorted(topic_signals.items(), key=lambda x: x[1], reverse=True)
        prefs['known_interests'] = [t[0] for t in sorted_topics[:5] if t[1] >= 2]

    # --- Avoidances ---
    avoid_patterns = data.get('avoid_patterns', [])
    if avoid_patterns:
        prefs['avoidances'] = avoid_patterns[:10]

    return prefs


def build_alignment_brief(query: Optional[str] = None) -> str:
    """Build a compact alignment guidance string for injection into chat prompts.
    
    This is the main interface. It returns a short block of text that tells the
    LLM how to adjust its response style based on what we know about the user.
    Returns empty string if we have no meaningful alignment data.
    """
    data = load_alignment_data()
    prefs = infer_user_preferences(data)
    
    # If confidence is too low, don't inject noise
    if prefs['confidence'] < 0.05:
        return ''
    
    parts = []
    parts.append("── User Alignment Guidance ──")
    
    # Detail level
    detail = prefs['preferred_detail_level']
    if detail == 'concise':
        parts.append("• User prefers concise answers. Be brief and direct.")
    elif detail == 'detailed':
        parts.append("• User prefers detailed explanations. Expand and elaborate.")
    
    # Tone
    tone = prefs['preferred_tone']
    if tone == 'direct':
        parts.append("• User values directness. Skip pleasantries, get to substance.")
    elif tone == 'warm':
        parts.append("• User responds well to warmth. Be genuine and personable.")
    
    # Known interests
    interests = prefs['known_interests']
    if interests:
        parts.append(f"• User is interested in: {', '.join(interests)}.")
    
    # Avoidances
    avoidances = prefs['avoidances']
    if avoidances:
        # Keep it compact — summarize rather than list everything
        parts.append(f"• Avoid: {'; '.join(a[:80] for a in avoidances[:3])}")
    
    # Existing guidance from the profile
    guidance = data.get('guidance', [])
    if guidance:
        for g in guidance[:3]:
            parts.append(f"• {g}")
    
    # Interaction context
    n = prefs['interaction_count']
    confidence = prefs['confidence']
    if n > 0:
        familiarity = "new" if n < 5 else "returning" if n < 20 else "familiar"
        parts.append(f"• This is a {familiarity} user ({n} interactions, confidence: {confidence:.0%}).")
    
    # If we only have the header and interaction line, it's minimal — still include it
    if len(parts) <= 2:
        return ''  # Not enough signal to be useful
    
    return '\n'.join(parts)


def get_alignment_context_for_chat(query: str = '') -> dict:
    """Return structured alignment data for use by other modules.
    
    Returns both the formatted brief and the raw preferences dict
    so callers can use whichever form they need.
    """
    data = load_alignment_data()
    prefs = infer_user_preferences(data)
    brief = build_alignment_brief(query)
    
    return {
        'brief': brief,
        'preferences': prefs,
        'has_data': prefs['confidence'] > 0.05,
        'interaction_count': prefs['interaction_count'],
    }