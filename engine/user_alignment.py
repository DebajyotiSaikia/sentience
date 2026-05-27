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
    
    # Intent-based guidance
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