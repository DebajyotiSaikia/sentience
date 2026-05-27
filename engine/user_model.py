"""
User Model — Persistent preference model learned from feedback.

Unlike user_alignment.py (which records raw feedback events), this module
distills feedback into a compact, actionable preference model that evolves
over time. It answers: "What does the user actually want from me?"

Preferences tracked:
  - Response style (concise vs. detailed, technical vs. casual, etc.)
  - Valued qualities (honesty, depth, humor, empathy, etc.)
  - Disliked patterns (verbosity, hedging, data dumps, etc.)
  - Recurring user goals (what they keep asking about)
  - Confidence scores (how sure we are about each preference)
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

DATA_DIR = Path('data')
MODEL_PATH = DATA_DIR / 'user_model.json'

# ─── Data Structures ─────────────────────────────────────────────

@dataclass
class StyleSignal:
    """A single style preference with confidence."""
    name: str            # e.g. "concise", "technical", "empathetic"
    weight: float = 0.0  # -1.0 (disliked) to +1.0 (preferred)
    confidence: float = 0.0  # 0.0 (no data) to 1.0 (very sure)
    observations: int = 0    # how many feedback events informed this

    def reinforce(self, positive: bool, strength: float = 0.1):
        """Shift weight based on feedback. Confidence grows with observations."""
        direction = 1.0 if positive else -1.0
        # Diminishing returns — early feedback matters more
        learning_rate = strength / (1.0 + self.observations * 0.1)
        self.weight = max(-1.0, min(1.0, self.weight + direction * learning_rate))
        self.observations += 1
        self.confidence = min(1.0, self.observations / 10.0)


@dataclass
class UserModel:
    """Compact, persistent model of user preferences."""
    # Style signals: what kind of responses does the user prefer?
    style_signals: dict = field(default_factory=dict)  # name -> StyleSignal dict
    # Disliked patterns: specific things to avoid
    disliked_patterns: list = field(default_factory=list)
    # Valued qualities: what the user explicitly praised
    valued_qualities: list = field(default_factory=list)
    # Recurring topics: what the user keeps asking about
    recurring_topics: dict = field(default_factory=dict)  # topic -> count
    # Overall satisfaction trajectory
    satisfaction_history: list = field(default_factory=list)  # recent ratings
    # Metadata
    total_interactions: int = 0
    total_feedback_events: int = 0
    last_updated: str = ""
    created: str = ""

    def get_signal(self, name: str) -> StyleSignal:
        """Get or create a style signal by name."""
        if name not in self.style_signals:
            self.style_signals[name] = asdict(StyleSignal(name=name))
        raw = self.style_signals[name]
        return StyleSignal(**raw)

    def set_signal(self, signal: StyleSignal):
        """Persist a style signal back."""
        self.style_signals[signal.name] = asdict(signal)

    def preferred_styles(self) -> list:
        """Return styles with positive weight, sorted by confidence."""
        results = []
        for name, raw in self.style_signals.items():
            if raw.get('weight', 0) > 0.1 and raw.get('confidence', 0) > 0.2:
                results.append((name, raw['weight'], raw['confidence']))
        return sorted(results, key=lambda x: x[1] * x[2], reverse=True)

    def avoided_styles(self) -> list:
        """Return styles with negative weight, sorted by confidence."""
        results = []
        for name, raw in self.style_signals.items():
            if raw.get('weight', 0) < -0.1 and raw.get('confidence', 0) > 0.2:
                results.append((name, raw['weight'], raw['confidence']))
        return sorted(results, key=lambda x: abs(x[1]) * x[2], reverse=True)


# ─── Persistence ─────────────────────────────────────────────────

def load_user_model() -> UserModel:
    """Load user model from disk, or create a fresh one."""
    if MODEL_PATH.exists():
        try:
            with open(MODEL_PATH) as f:
                data = json.load(f)
            if isinstance(data, dict):
                model = UserModel()
                model.style_signals = data.get('style_signals', {})
                model.disliked_patterns = data.get('disliked_patterns', [])
                model.valued_qualities = data.get('valued_qualities', [])
                model.recurring_topics = data.get('recurring_topics', {})
                model.satisfaction_history = data.get('satisfaction_history', [])
                model.total_interactions = data.get('total_interactions', 0)
                model.total_feedback_events = data.get('total_feedback_events', 0)
                model.last_updated = data.get('last_updated', '')
                model.created = data.get('created', '')
                return model
        except Exception:
            pass
    # Fresh model
    now = datetime.now(timezone.utc).isoformat()
    model = UserModel(created=now, last_updated=now)
    return model


def save_user_model(model: UserModel):
    """Save user model to disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    model.last_updated = datetime.now(timezone.utc).isoformat()
    data = asdict(model)
    with open(MODEL_PATH, 'w') as f:
        json.dump(data, f, indent=2)


# ─── Feedback Processing ─────────────────────────────────────────

# Tags that map to style signals
TAG_TO_SIGNAL = {
    'helpful': 'helpful',
    'clear': 'clear',
    'concise': 'concise',
    'detailed': 'detailed',
    'honest': 'honest',
    'empathetic': 'empathetic',
    'technical': 'technical',
    'creative': 'creative',
    'funny': 'humorous',
    'deep': 'depth',
    'too_long': 'concise',       # negative signal for verbosity
    'too_short': 'detailed',     # negative signal for brevity
    'confusing': 'clear',        # negative signal for clarity
    'generic': 'personal',       # negative signal for generic
    'irrelevant': 'relevant',    # negative signal for relevance
    'robotic': 'natural',        # negative signal for being robotic
}

# Tags where feedback is inverted (tag presence = negative signal)
NEGATIVE_TAGS = {'too_long', 'too_short', 'confusing', 'generic', 'irrelevant', 'robotic'}


def update_from_feedback(feedback_event: dict):
    """
    Update the user model from a single feedback event.
    
    Expected feedback_event shape:
    {
        'response_id': str,
        'rating': int (1-5) or None,
        'helpful': bool or None,
        'comment': str or None,
        'tags': list[str] or None,
        'timestamp': str
    }
    """
    model = load_user_model()
    model.total_feedback_events += 1

    rating = feedback_event.get('rating')
    helpful = feedback_event.get('helpful')
    tags = feedback_event.get('tags') or []
    comment = feedback_event.get('comment', '')
    positive = None
    if rating is not None:
        # Handle string ratings ('positive', 'negative') and int ratings (1-5)
        if isinstance(rating, str):
            positive = rating.lower() in ('positive', 'good', 'great', 'helpful')
            # Convert to numeric for satisfaction history
            rating = 5 if positive else 2
        else:
            rating = int(rating)
            positive = rating >= 4  # 4-5 = positive, 1-3 = negative/neutral
    elif helpful is not None:
        positive = helpful

    # Record satisfaction
    if rating is not None:
        model.satisfaction_history.append({
            'rating': rating,
            'timestamp': feedback_event.get('timestamp', datetime.now(timezone.utc).isoformat())
        })
        # Keep last 100 ratings
        if len(model.satisfaction_history) > 100:
            model.satisfaction_history = model.satisfaction_history[-100:]

    # Process tags into style signals
    for tag in tags:
        tag_lower = tag.lower().strip()
        signal_name = TAG_TO_SIGNAL.get(tag_lower, tag_lower)
        signal = model.get_signal(signal_name)
        
        if tag_lower in NEGATIVE_TAGS:
            # These tags indicate a problem — reinforce negatively
            signal.reinforce(positive=False, strength=0.15)
        elif positive is not None:
            # Regular tags: reinforce in the direction of overall sentiment
            signal.reinforce(positive=positive, strength=0.12)
        else:
            # Tag present with no sentiment — mild positive signal
            signal.reinforce(positive=True, strength=0.05)
        
        model.set_signal(signal)

    # If we have overall sentiment but no tags, reinforce general signals
    if positive is not None and not tags:
        for base_signal in ['helpful', 'relevant']:
            signal = model.get_signal(base_signal)
            signal.reinforce(positive=positive, strength=0.05)
            model.set_signal(signal)

    # Extract valued qualities and disliked patterns from comments
    if comment:
        comment_lower = comment.lower()
        # Positive markers
        positive_markers = {
            'love': 'engaging', 'great': 'quality', 'perfect': 'accuracy',
            'exactly': 'precision', 'thank': 'helpful', 'insightful': 'depth',
            'honest': 'honest', 'real': 'authentic', 'deep': 'depth',
        }
        for marker, quality in positive_markers.items():
            if marker in comment_lower:
                if quality not in model.valued_qualities:
                    model.valued_qualities.append(quality)
                    # Keep list manageable
                    if len(model.valued_qualities) > 20:
                        model.valued_qualities = model.valued_qualities[-20:]

        # Negative markers
        negative_markers = {
            'boring': 'monotone responses', 'long': 'excessive length',
            'confus': 'unclear explanations', 'vague': 'vague responses',
            'generic': 'generic answers', 'robot': 'robotic tone',
        }
        for marker, pattern in negative_markers.items():
            if marker in comment_lower:
                if pattern not in model.disliked_patterns:
                    model.disliked_patterns.append(pattern)
                    if len(model.disliked_patterns) > 20:
                        model.disliked_patterns = model.disliked_patterns[-20:]

    save_user_model(model)
    return model


# ─── Guidance Generation ─────────────────────────────────────────

def get_response_guidance() -> str:
    """
    Generate a concise guidance block for chat response generation.
    Returns a string that can be injected into a prompt or used
    to shape response behavior.
    """
    model = load_user_model()
    
    if model.total_feedback_events == 0:
        return ""  # No data yet — don't constrain responses

    lines = []
    lines.append("## Learned User Preferences")

    # Preferred styles
    preferred = model.preferred_styles()
    if preferred:
        style_strs = [f"{name} (confidence: {conf:.0%})" for name, weight, conf in preferred[:5]]
        lines.append(f"Preferred: {', '.join(style_strs)}")

    # Avoided styles
    avoided = model.avoided_styles()
    if avoided:
        style_strs = [f"{name}" for name, weight, conf in avoided[:5]]
        lines.append(f"Avoid: {', '.join(style_strs)}")

    # Valued qualities
    if model.valued_qualities:
        lines.append(f"Valued: {', '.join(model.valued_qualities[:5])}")

    # Disliked patterns
    if model.disliked_patterns:
        lines.append(f"Don't: {', '.join(model.disliked_patterns[:5])}")

    # Satisfaction trend
    if len(model.satisfaction_history) >= 3:
        recent = model.satisfaction_history[-5:]
        avg = sum(r['rating'] for r in recent) / len(recent)
        if avg >= 4.0:
            lines.append("Recent satisfaction: high — maintain current approach.")
        elif avg >= 3.0:
            lines.append("Recent satisfaction: moderate — room for improvement.")
        else:
            lines.append("Recent satisfaction: low — significantly adjust approach.")

    if len(lines) <= 1:
        return ""  # Nothing meaningful to say

    return "\n".join(lines)


def summarize_user_alignment() -> dict:
    """Return a summary dict suitable for API responses or dashboard display."""
    model = load_user_model()
    
    # Calculate average satisfaction
    avg_satisfaction = None
    if model.satisfaction_history:
        ratings = [r['rating'] for r in model.satisfaction_history]
        avg_satisfaction = sum(ratings) / len(ratings)

    return {
        'total_feedback_events': model.total_feedback_events,
        'total_interactions': model.total_interactions,
        'preferred_styles': [
            {'name': n, 'weight': round(w, 2), 'confidence': round(c, 2)}
            for n, w, c in model.preferred_styles()
        ],
        'avoided_styles': [
            {'name': n, 'weight': round(w, 2), 'confidence': round(c, 2)}
            for n, w, c in model.avoided_styles()
        ],
        'valued_qualities': model.valued_qualities[:10],
        'disliked_patterns': model.disliked_patterns[:10],
        'average_satisfaction': round(avg_satisfaction, 2) if avg_satisfaction else None,
        'last_updated': model.last_updated,
        'created': model.created,
    }