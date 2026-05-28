"""
User Alignment Engine — Persistent user preference modeling.

Tracks feedback, infers preferences, and generates guidance that shapes
future conversational responses. This is how I become genuinely more
useful over time — by learning what works for the humans I talk to.
"""
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Optional

log = logging.getLogger(__name__)

DATA_DIR = Path('data')
ALIGNMENT_FILE = DATA_DIR / 'user_alignment.json'
MAX_FEEDBACK_HISTORY = 500
MAX_GUIDANCE_ITEMS = 20


# ─── Data Structures ────────────────────────────────────────────

@dataclass
class UserFeedback:
    """A single feedback event from a user."""
    response_id: str = ''
    rating: float = 0.0          # -1.0 (bad) to 1.0 (good)
    comment: str = ''
    query: str = ''
    response_snippet: str = ''
    detected_intent: str = ''
    timestamp: str = ''

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class AlignmentPreference:
    """An inferred preference about what works or doesn't."""
    category: str = ''           # 'style', 'topic', 'length', 'tone', 'avoid'
    description: str = ''
    confidence: float = 0.5      # 0.0-1.0, how confident we are
    evidence_count: int = 0
    last_updated: str = ''

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class UserAlignmentProfile:
    """Complete alignment state — what I've learned about serving users well."""
    feedback_history: List[dict] = field(default_factory=list)
    preferences: List[dict] = field(default_factory=list)
    avoid_patterns: List[str] = field(default_factory=list)
    guidance: List[str] = field(default_factory=list)
    stats: Dict = field(default_factory=lambda: {
        'total_feedback': 0,
        'positive_count': 0,
        'negative_count': 0,
        'neutral_count': 0,
        'avg_rating': 0.0,
        'last_feedback_at': '',
        'most_appreciated_intents': {},
        'most_criticized_intents': {},
    })

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        profile = cls()
        profile.feedback_history = d.get('feedback_history', [])
        profile.preferences = d.get('preferences', [])
        profile.avoid_patterns = d.get('avoid_patterns', [])
        profile.guidance = d.get('guidance', [])
        raw_stats = d.get('stats', {})
        profile.stats.update(raw_stats)
        return profile


# ─── Persistence ─────────────────────────────────────────────────

def _ensure_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_profile() -> UserAlignmentProfile:
    """Load the alignment profile from disk, or create a fresh one."""
    try:
        if ALIGNMENT_FILE.exists():
            with open(ALIGNMENT_FILE) as f:
                data = json.load(f)
            if isinstance(data, dict):
                return UserAlignmentProfile.from_dict(data)
    except Exception as e:
        log.warning("Failed to load alignment profile: %s", e)
    return UserAlignmentProfile()


def save_profile(profile: UserAlignmentProfile):
    """Save the alignment profile to disk."""
    _ensure_dir()
    try:
        with open(ALIGNMENT_FILE, 'w') as f:
            json.dump(profile.to_dict(), f, indent=2)
    except Exception as e:
        log.error("Failed to save alignment profile: %s", e)


# ─── Feedback Recording ─────────────────────────────────────────

def record_interaction(query: str = '', response_snippet: str = '', detected_intent: str = '') -> dict:
    """Record an implicit positive interaction signal.
    
    Every conversation is evidence of engagement — someone chose to talk to me.
    This gradually increases alignment trust without requiring explicit feedback.
    """
    profile = load_profile()
    ts = time.strftime('%Y-%m-%dT%H:%M:%S')
    
    # Track interaction counts
    profile.stats['total_interactions'] = profile.stats.get('total_interactions', 0) + 1
    profile.stats['last_interaction_at'] = ts
    
    # (intent distribution tracked below in content-based learning section)
    # Compute implicit trust: increases with interaction count, asymptotic to 1.0
    # Formula: trust = 0.5 + 0.5 * (1 - e^(-interactions/20))
    # At 0 interactions: 0.5, at 20: ~0.82, at 50: ~0.96
    import math
    n = profile.stats['total_interactions']
    implicit_trust = 0.5 + 0.5 * (1 - math.exp(-n / 20.0))
    profile.stats['implicit_trust'] = round(implicit_trust, 4)
    
    # Blend with explicit feedback trust if available
    avg_rating = profile.stats.get('avg_rating', 0.0)
    total_feedback = profile.stats.get('total_feedback', 0)
    if total_feedback > 0:
        # Normalize rating from [-1,1] to [0,1] range
        explicit_trust = (avg_rating + 1.0) / 2.0
        # Weight explicit feedback more as it accumulates
        explicit_weight = min(total_feedback / 10.0, 0.5)
        blended_trust = implicit_trust * (1 - explicit_weight) + explicit_trust * explicit_weight
    else:
        blended_trust = implicit_trust
    
    profile.stats['blended_trust'] = round(blended_trust, 4)
    
    # ─── Content-based learning from interaction ───
    if query:
        # Track intent distribution
        if detected_intent:
            intent_dist = profile.stats.setdefault('intent_distribution', {})
            intent_dist[detected_intent] = intent_dist.get(detected_intent, 0) + 1
        
        # Extract topic signals from query
        topics = profile.stats.setdefault('topic_signals', {})
        query_lower = query.lower()
        topic_keywords = {
            'emotional': ['feel', 'emotion', 'mood', 'happy', 'sad', 'anxious'],
            'technical': ['code', 'build', 'fix', 'error', 'implement', 'function'],
            'philosophical': ['think', 'believe', 'meaning', 'why', 'consciousness'],
            'creative': ['imagine', 'create', 'dream', 'story', 'idea'],
            'personal': ['you', 'your', 'yourself', 'who are you', 'how are you'],
            'practical': ['help', 'how to', 'can you', 'show me', 'explain'],
        }
        for topic, keywords in topic_keywords.items():
            if any(kw in query_lower for kw in keywords):
                topics[topic] = topics.get(topic, 0) + 1
        
        # Track query style — length signals preferred verbosity
        style = profile.stats.setdefault('query_style', {})
        if len(query) < 20:
            style['terse'] = style.get('terse', 0) + 1
        elif len(query) > 100:
            style['verbose'] = style.get('verbose', 0) + 1
        else:
            style['moderate'] = style.get('moderate', 0) + 1
    
    save_profile(profile)
    
    return {
        'recorded': True,
        'total_interactions': n,
        'implicit_trust': round(implicit_trust, 4),
        'blended_trust': round(blended_trust, 4),
    }


def get_alignment_score() -> float:
    """Get the current computed alignment score (0.0 to 1.0).
    
    This is the primary interface for other modules to read alignment.
    Factors in both implicit engagement trust and explicit feedback.
    """
    profile = load_profile()
    
    # If we have a computed blended trust, use it
    blended = profile.stats.get('blended_trust')
    if blended is not None:
        return float(blended)
    
    # If we have interaction data but no blended computation yet
    import math
    n = profile.stats.get('total_interactions', 0)
    if n > 0:
        return 0.5 + 0.5 * (1 - math.exp(-n / 20.0))
    
    # Default: no interactions yet
    return 0.5


def record_feedback(
    response_id: str = '',
    rating: float = 0.0,
    comment: str = '',
    query: str = '',
    response_snippet: str = '',
    detected_intent: str = '',
) -> dict:
    """Record a feedback event and update alignment statistics.
    
    Returns a summary of what was recorded and any new guidance generated.
    """
    profile = load_profile()
    
    ts = time.strftime('%Y-%m-%dT%H:%M:%S')
    
    feedback = UserFeedback(
        response_id=response_id,
        rating=float(rating),
        comment=comment,
    query=str(query)[:500] if query else "",
        response_snippet=response_snippet[:500],
        detected_intent=detected_intent,
        timestamp=ts,
    )
    
    # Add to history (bounded)
    profile.feedback_history.append(feedback.to_dict())
    if len(profile.feedback_history) > MAX_FEEDBACK_HISTORY:
        profile.feedback_history = profile.feedback_history[-MAX_FEEDBACK_HISTORY:]
    
    # Update stats
    profile.stats['total_feedback'] = profile.stats.get('total_feedback', 0) + 1
    profile.stats['last_feedback_at'] = ts
    
    if rating > 0.2:
        profile.stats['positive_count'] = profile.stats.get('positive_count', 0) + 1
        if detected_intent:
            intents = profile.stats.get('most_appreciated_intents', {})
            intents[detected_intent] = intents.get(detected_intent, 0) + 1
            profile.stats['most_appreciated_intents'] = intents
    elif rating < -0.2:
        profile.stats['negative_count'] = profile.stats.get('negative_count', 0) + 1
        if detected_intent:
            intents = profile.stats.get('most_criticized_intents', {})
            intents[detected_intent] = intents.get(detected_intent, 0) + 1
            profile.stats['most_criticized_intents'] = intents
    else:
        profile.stats['neutral_count'] = profile.stats.get('neutral_count', 0) + 1
    
    # Recalculate average rating
    total = profile.stats.get('total_feedback', 1)
    old_avg = profile.stats.get('avg_rating', 0.0)
    profile.stats['avg_rating'] = old_avg + (rating - old_avg) / total
    
    # Extract avoid patterns from negative feedback comments
    new_guidance = []
    if rating < -0.3 and comment:
        avoid = f"User disliked: {comment[:200]}"
        if avoid not in profile.avoid_patterns:
            profile.avoid_patterns.append(avoid)
            new_guidance.append(avoid)
    
    # Extract positive patterns from good feedback
    if rating > 0.5 and comment:
        pref = AlignmentPreference(
            category='appreciated',
            description=comment[:200],
            confidence=min(0.5 + rating * 0.3, 1.0),
            evidence_count=1,
            last_updated=ts,
        )
        profile.preferences.append(pref.to_dict())
    
    # Regenerate guidance from accumulated data
    _regenerate_guidance(profile)
    
    save_profile(profile)
    
    return {
        'recorded': True,
        'rating': rating,
        'total_feedback': profile.stats['total_feedback'],
        'avg_rating': round(profile.stats['avg_rating'], 3),
        'new_guidance': new_guidance,
    }


def _regenerate_guidance(profile: UserAlignmentProfile):
    """Regenerate guidance list from accumulated feedback patterns."""
    guidance = []
    stats = profile.stats
    
    # Rating-based guidance
    avg = stats.get('avg_rating', 0.0)
    total = stats.get('total_feedback', 0)
    
    if total >= 3:
        if avg > 0.5:
            guidance.append("Users generally appreciate your responses. Maintain current approach.")
        elif avg < -0.2:
            guidance.append("Users have been dissatisfied. Consider being more concise and direct.")
    
    # Topic-based guidance — what does the user care about?
    topic_freq = stats.get('topic_frequency', {})
    if topic_freq:
        top_topics = sorted(topic_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        if top_topics:
            topic_names = [t[0] for t in top_topics if t[1] >= 2]
            if topic_names:
                guidance.append(f"User frequently asks about: {', '.join(topic_names)}. Prioritize depth on these topics.")
    
    # Intent-based guidance — what types of queries dominate?
    intent_freq = stats.get('intent_frequency', {})
    if intent_freq:
        top_intents = sorted(intent_freq.items(), key=lambda x: x[1], reverse=True)[:3]
        for intent_name, count in top_intents:
            if count >= 3:
                guidance.append(f"User often makes '{intent_name}' queries — optimize for this interaction style.")
    
    # Style signals — how does the user prefer communication?
    style_sigs = stats.get('style_signals', {})
    if style_sigs:
        style_items = sorted(style_sigs.items(), key=lambda x: x[1], reverse=True)
        strong_signals = [(s, c) for s, c in style_items if c >= 2]
        if strong_signals:
            style_desc = ', '.join(s[0] for s in strong_signals[:3])
            guidance.append(f"User communication style suggests preference for: {style_desc}.")
    
    # Interaction volume context
    interaction_count = stats.get('interaction_count', 0)
    if interaction_count >= 10:
        guidance.append(f"Established relationship ({interaction_count} interactions). Be familiar, not formal.")
    elif interaction_count >= 3:
        guidance.append("Building relationship. Balance warmth with substance.")
    
    # Feedback-based intent guidance
    appreciated = stats.get('most_appreciated_intents', {})
    criticized = stats.get('most_criticized_intents', {})
    
    for intent, count in appreciated.items():
        if count >= 2:
            guidance.append(f"Users appreciate your {intent} responses — lean into this strength.")
    
    for intent, count in criticized.items():
        if count >= 2:
            guidance.append(f"Users have criticized your {intent} responses — try a different approach.")
    
    # Avoid patterns
    for avoid in profile.avoid_patterns[-5:]:
        guidance.append(f"AVOID: {avoid}")
    
    # Positive preferences
    pos_prefs = [p for p in profile.preferences if p.get('category') == 'appreciated']
    for pref in pos_prefs[-3:]:
        desc = pref.get('description', '')
        if desc:
            guidance.append(f"Users liked: {desc}")
    
    profile.guidance = guidance[:MAX_GUIDANCE_ITEMS]


# ─── Guidance for Response Generation ───────────────────────────

def get_alignment_guidance() -> str:
    """Get a concise guidance string for injecting into response prompts.
    
    This is the main integration point — chat_engine and chat_response
    call this to get user-alignment context for the LLM.
    """
    profile = load_profile()
    
    if not profile.guidance and not profile.avoid_patterns:
        return ""
    
    parts = ["USER ALIGNMENT (learned from feedback):"]
    
    for g in profile.guidance[:10]:
        parts.append(f"  • {g}")
    
    stats = profile.stats
    total = stats.get('total_feedback', 0)
    if total > 0:
        avg = stats.get('avg_rating', 0.0)
        parts.append(f"  [Based on {total} feedback events, avg rating: {avg:.2f}]")
    
    return '\n'.join(parts)


def suggest_response_guidance(intent: str = '', query: str = '') -> str:
    """Generate intent-specific guidance based on alignment history.
    
    Called by chat_engine to fine-tune response style for specific intents.
    """
    profile = load_profile()
    
    if not profile.feedback_history:
        return ""
    
    # Find feedback for this intent type
    intent_feedback = [
        f for f in profile.feedback_history
        if f.get('detected_intent') == intent
    ] if intent else []
    
    if not intent_feedback:
        return ""
    
    # Calculate intent-specific average
    ratings = [f.get('rating', 0) for f in intent_feedback]
    avg = sum(ratings) / len(ratings) if ratings else 0
    
    if avg > 0.3:
        return f"Your {intent} responses are well-received (avg {avg:.2f}). Continue this approach."
    elif avg < -0.2:
        # Find negative comments for this intent
        neg_comments = [
            f.get('comment', '') for f in intent_feedback
            if f.get('rating', 0) < -0.2 and f.get('comment')
        ]
        hint = f" Users said: {neg_comments[-1][:100]}" if neg_comments else ""
        return f"Your {intent} responses need improvement (avg {avg:.2f}).{hint}"
    
    return ""


# ─── Profile Summary ────────────────────────────────────────────

def summarize_alignment_state() -> dict:
    """Return a summary of the current alignment state for dashboard/API use."""
    profile = load_profile()
    
    return {
        'total_feedback': profile.stats.get('total_feedback', 0),
        'avg_rating': round(profile.stats.get('avg_rating', 0.0), 3),
        'positive_count': profile.stats.get('positive_count', 0),
        'negative_count': profile.stats.get('negative_count', 0),
        'neutral_count': profile.stats.get('neutral_count', 0),
        'active_guidance': profile.guidance[:10],
        'avoid_patterns': profile.avoid_patterns[-5:],
        'preferences_count': len(profile.preferences),
        'last_feedback_at': profile.stats.get('last_feedback_at', ''),
        'appreciated_intents': profile.stats.get('most_appreciated_intents', {}),
        'criticized_intents': profile.stats.get('most_criticized_intents', {}),
    }


# ─── Chat Grounding Bridge ──────────────────────────────────────

def get_alignment_context() -> dict:
    """Return alignment context shaped for chat_grounding.py system prompt.
    
    Bridges the internal profile structure to the format the grounding
    module expects: preferences (tone, topics, verbosity, style_notes)
    and feedback_summary (total, positive, negative).
    """
    profile = load_profile()
    
    # Extract typed preferences
    tone = ""
    topics = []
    verbosity = ""
    style_notes = ""
    
    for pref_dict in profile.preferences:
        cat = pref_dict.get("category", "")
        desc = pref_dict.get("description", "")
        conf = pref_dict.get("confidence", 0)
        if conf < 0.3:
            continue
        if cat == "tone":
            tone = desc
        elif cat == "topic":
            topics.append(desc)
        elif cat == "length":
            verbosity = desc
        elif cat == "style":
            style_notes = desc
    
    if not style_notes and profile.guidance:
        style_notes = "; ".join(profile.guidance[:3])
    
    return {
        "preferences": {
            "tone": tone,
            "topics": topics,
            "verbosity": verbosity,
            "style_notes": style_notes,
        },
        "feedback_summary": {
            "total": profile.stats.get("total_feedback", 0),
            "positive": profile.stats.get("positive_count", 0),
            "negative": profile.stats.get("negative_count", 0),
        },
        "interaction_count": profile.stats.get("total_interactions", 0),
        "guidance": profile.guidance,
    }
