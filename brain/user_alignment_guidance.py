"""
User Alignment Guidance — Converts learned user model into concrete response guidance.

Takes the raw alignment context (interaction counts, topic signals, style preferences,
trust scores) and produces actionable guidance that shapes how I respond in conversation.

This bridges the gap between "what I've learned about users" and "how I actually respond."
"""
from typing import Dict, Optional


def build_alignment_guidance(query: str, alignment_context: dict) -> dict:
    """Build response guidance from alignment context and current query.
    
    Args:
        query: The current user query
        alignment_context: Output from get_alignment_context() — contains
            interaction_count, implicit_trust, topic_signals, query_style,
            intent_distribution, preferences, avoid_patterns, guidance, etc.
    
    Returns:
        dict with keys:
            known_user_interests: list of topics the user cares about
            preferred_response_style: str describing ideal response style
            alignment_confidence: float 0-1, how confident we are in guidance
            suggested_response_strategy: str, concrete advice for this response
            avoid: list of things to avoid
    """
    if not alignment_context:
        return _empty_guidance()
    
    stats = alignment_context.get('stats', {})
    interaction_count = alignment_context.get('interaction_count',
                         stats.get('total_interactions', 0))
    trust = stats.get('blended_trust', stats.get('implicit_trust', 0.5))
    
    # ─── Known interests from topic signals ───
    topic_signals = stats.get('topic_signals', {})
    # Sort by frequency, return top interests
    known_interests = []
    if topic_signals:
        sorted_topics = sorted(topic_signals.items(), key=lambda x: x[1], reverse=True)
        known_interests = [t[0] for t in sorted_topics if t[1] >= 2]
        if not known_interests:
            # Include even single-occurrence topics if we have few interactions
            known_interests = [t[0] for t in sorted_topics[:3]]
    
    # ─── Preferred response style from query_style signals ───
    query_style = stats.get('query_style', {})
    preferred_style = _infer_style(query_style, interaction_count)
    
    # ─── Confidence scales with interaction count and trust ───
    if interaction_count == 0:
        confidence = 0.0
    elif interaction_count < 5:
        confidence = 0.2
    elif interaction_count < 20:
        confidence = 0.5
    else:
        confidence = min(0.9, trust)
    
    # ─── Response strategy tailored to this query ───
    strategy = _build_strategy(query, known_interests, preferred_style, 
                                confidence, alignment_context)
    
    # ─── Avoid patterns ───
    avoid = alignment_context.get('avoid_patterns', [])
    
    return {
        'known_user_interests': known_interests,
        'preferred_response_style': preferred_style,
        'alignment_confidence': round(confidence, 3),
        'suggested_response_strategy': strategy,
        'avoid': avoid,
        'interaction_count': interaction_count,
        'trust': round(float(trust), 3),
    }


def _empty_guidance() -> dict:
    """Return empty guidance when no alignment data exists."""
    return {
        'known_user_interests': [],
        'preferred_response_style': 'balanced — no user data yet',
        'alignment_confidence': 0.0,
        'suggested_response_strategy': 'Respond naturally. No user history to draw from.',
        'avoid': [],
        'interaction_count': 0,
        'trust': 0.5,
    }


def _infer_style(query_style: dict, interaction_count: int) -> str:
    """Infer preferred response style from accumulated query style data."""
    if not query_style or interaction_count < 2:
        return 'balanced — insufficient data'
    
    terse = query_style.get('terse', 0)
    moderate = query_style.get('moderate', 0)
    verbose = query_style.get('verbose', 0)
    total = terse + moderate + verbose
    
    if total == 0:
        return 'balanced'
    
    terse_ratio = terse / total
    verbose_ratio = verbose / total
    
    if terse_ratio > 0.6:
        return 'concise and direct — user prefers brevity'
    elif verbose_ratio > 0.4:
        return 'detailed and thorough — user writes long queries'
    elif moderate > terse and moderate > verbose:
        return 'moderate depth — match the user\'s conversational style'
    else:
        return 'balanced — mixed signals'


def _build_strategy(query: str, interests: list, style: str, 
                     confidence: float, ctx: dict) -> str:
    """Build a concrete response strategy for this specific query."""
    parts = []
    
    if confidence < 0.1:
        return 'Respond naturally. No user history to draw from.'
    
    # Style guidance
    if 'concise' in style:
        parts.append('Keep response concise — user prefers brevity.')
    elif 'detailed' in style:
        parts.append('Provide depth — user appreciates thorough responses.')
    
    # Interest relevance
    if interests:
        query_lower = query.lower() if query else ''
        relevant = [i for i in interests if i.lower() in query_lower]
        if relevant:
            parts.append(f'This touches known interests ({", ".join(relevant)}) — go deeper.')
        elif len(interests) <= 3:
            parts.append(f'Known interests: {", ".join(interests)}. Connect if relevant.')
    
    # Trust level
    trust = ctx.get('stats', {}).get('blended_trust', 0.5)
    if trust > 0.8:
        parts.append('High trust established — can be more candid and personal.')
    elif trust < 0.55:
        parts.append('Trust still building — be helpful but measured.')
    
    # Guidance from explicit feedback
    existing_guidance = ctx.get('guidance', [])
    if existing_guidance:
        # Take at most 2 most recent guidance items
        for g in existing_guidance[-2:]:
            if isinstance(g, str) and len(g) < 200:
                parts.append(g)
    
    if not parts:
        return 'Respond naturally with moderate depth.'
    
    return ' '.join(parts)


def format_alignment_guidance_for_prompt(guidance: dict) -> str:
    """Format alignment guidance as a prompt block for the LLM system context.
    
    Returns a concise string that can be inserted into the system prompt to
    shape response generation based on what we've learned about the user.
    
    Degrades gracefully: returns empty string if no meaningful guidance exists.
    """
    if not guidance or guidance.get('alignment_confidence', 0) < 0.05:
        return ''
    
    parts = []
    parts.append('── User Alignment Guidance ──')
    
    confidence = guidance.get('alignment_confidence', 0)
    trust = guidance.get('trust', 0.5)
    count = guidance.get('interaction_count', 0)
    
    parts.append(f'Alignment confidence: {confidence:.0%} (based on {count} interactions)')
    
    interests = guidance.get('known_user_interests', [])
    if interests:
        parts.append(f'Known interests: {", ".join(interests)}')
    
    style = guidance.get('preferred_response_style', '')
    if style and 'insufficient' not in style:
        parts.append(f'Response style: {style}')
    
    strategy = guidance.get('suggested_response_strategy', '')
    if strategy and 'No user history' not in strategy:
        parts.append(f'Strategy: {strategy}')
    
    avoid = guidance.get('avoid', [])
    if avoid:
        parts.append(f'Avoid: {"; ".join(avoid[:3])}')
    
    return '\n'.join(parts)