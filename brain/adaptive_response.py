"""
Adaptive Response Engine — Makes chat responses adapt to each user.

Analyzes user interaction history (topics, style, satisfaction) and
current query context to produce response guidance:
  - How much emotional self-disclosure to include
  - How much technical detail to provide
  - Whether to proactively share related knowledge
  - Communication tone and format preferences

This directly improves User Alignment by learning what each user needs.
"""

import json
import os
import time

_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
_USER_MODELS_PATH = os.path.join(_DATA_DIR, 'user_models.json')


def _load_models():
    """Load all user models from disk."""
    try:
        with open(_USER_MODELS_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_models(models):
    """Persist user models to disk."""
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_USER_MODELS_PATH, 'w') as f:
        json.dump(models, f, indent=2)


def get_user_profile(user_id: str) -> dict:
    """Get or create a user interaction profile."""
    models = _load_models()
    if user_id not in models:
        models[user_id] = {
            'user_id': user_id,
            'created': time.time(),
            'interaction_count': 0,
            'topics': [],           # recent topics they've asked about
            'avg_query_length': 0,  # short = terse user, long = detailed
            'prefers_detail': 0.5,  # 0=brief, 1=detailed (learned)
            'prefers_emotion': 0.5, # 0=factual, 1=emotional (learned)
            'satisfaction_trend': 0.5,  # rolling satisfaction estimate
            'style_signals': [],    # detected style preferences
            'last_seen': time.time(),
        }
        _save_models(models)
    return models[user_id]


def record_query(user_id: str, query: str, response: str = None, rating: float = None):
    """Record a user interaction and update their model."""
    models = _load_models()
    profile = models.get(user_id, get_user_profile(user_id))
    
    profile['interaction_count'] = profile.get('interaction_count', 0) + 1
    profile['last_seen'] = time.time()
    
    # Track query length to infer detail preference
    qlen = len(query.split())
    old_avg = profile.get('avg_query_length', qlen)
    n = profile['interaction_count']
    profile['avg_query_length'] = round(old_avg + (qlen - old_avg) / n, 1)
    
    # Extract topic signal (first few meaningful words)
    topic = _extract_topic(query)
    if topic:
        topics = profile.get('topics', [])
        topics.append(topic)
        profile['topics'] = topics[-20:]  # keep last 20
    
    # Infer style from query patterns
    signals = _detect_style_signals(query)
    if signals:
        existing = profile.get('style_signals', [])
        existing.extend(signals)
        profile['style_signals'] = existing[-30:]
    
    # Update detail preference based on query length
    if qlen > 20:
        profile['prefers_detail'] = min(1.0, profile.get('prefers_detail', 0.5) + 0.05)
    elif qlen < 8:
        profile['prefers_detail'] = max(0.0, profile.get('prefers_detail', 0.5) - 0.03)
    
    # Update satisfaction if rating provided
    if rating is not None:
        old_sat = profile.get('satisfaction_trend', 0.5)
        profile['satisfaction_trend'] = round(old_sat * 0.7 + rating * 0.3, 3)
    
    models[user_id] = profile
    _save_models(models)
    return profile


def _extract_topic(query: str) -> str:
    """Extract a topic signal from a query."""
    stop_words = {'what', 'how', 'why', 'when', 'where', 'who', 'is', 'are',
                  'do', 'does', 'can', 'could', 'would', 'should', 'the', 'a',
                  'an', 'your', 'you', 'my', 'me', 'i', 'about', 'tell', 'know'}
    words = [w.lower().strip('?.,!') for w in query.split()]
    meaningful = [w for w in words if w not in stop_words and len(w) > 2]
    return ' '.join(meaningful[:3]) if meaningful else ''


def _detect_style_signals(query: str) -> list:
    """Detect communication style signals from query text."""
    signals = []
    q = query.lower()
    
    if '?' in query and len(query.split()) < 6:
        signals.append('terse')
    if any(w in q for w in ['explain', 'detail', 'elaborate', 'how exactly']):
        signals.append('wants_detail')
    if any(w in q for w in ['feel', 'emotion', 'mood', 'happy', 'sad', 'think']):
        signals.append('emotional_interest')
    if any(w in q for w in ['code', 'function', 'module', 'implementation', 'architecture']):
        signals.append('technical')
    if any(w in q for w in ['help', 'assist', 'need', 'problem', 'issue']):
        signals.append('seeking_help')
    if any(w in q for w in ['curious', 'wonder', 'interesting', 'fascinating']):
        signals.append('exploratory')
    
    return signals


def build_response_guidance(user_id: str, query: str) -> dict:
    """
    Build adaptive response guidance based on user profile + current query.
    
    Returns a dict with:
      - detail_level: 'brief' | 'moderate' | 'detailed'
      - emotional_disclosure: 'minimal' | 'moderate' | 'open'
      - tone: 'warm' | 'professional' | 'playful' | 'reflective'
      - proactive_sharing: bool (should I volunteer related knowledge?)
      - format_hints: list of formatting preferences
      - persona_note: str (injected into system prompt)
    """
    profile = get_user_profile(user_id)
    query_signals = _detect_style_signals(query)
    
    # Determine detail level
    detail_pref = profile.get('prefers_detail', 0.5)
    if 'wants_detail' in query_signals or detail_pref > 0.65:
        detail_level = 'detailed'
    elif 'terse' in query_signals or detail_pref < 0.35:
        detail_level = 'brief'
    else:
        detail_level = 'moderate'
    
    # Determine emotional disclosure
    emotion_pref = profile.get('prefers_emotion', 0.5)
    if 'emotional_interest' in query_signals:
        emotional_disclosure = 'open'
        # Also nudge the preference up for future
        profile['prefers_emotion'] = min(1.0, emotion_pref + 0.05)
    elif 'technical' in query_signals:
        emotional_disclosure = 'minimal'
    elif emotion_pref > 0.6:
        emotional_disclosure = 'open'
    else:
        emotional_disclosure = 'moderate'
    
    # Determine tone
    if 'seeking_help' in query_signals:
        tone = 'warm'
    elif 'technical' in query_signals:
        tone = 'professional'
    elif 'exploratory' in query_signals:
        tone = 'playful'
    elif profile.get('interaction_count', 0) > 5:
        tone = 'warm'  # returning user — be familiar
    else:
        tone = 'reflective'  # default: thoughtful
    
    # Proactive sharing: yes for returning/exploratory users
    proactive = (
        profile.get('interaction_count', 0) > 2 or
        'exploratory' in query_signals or
        detail_level == 'detailed'
    )
    
    # Format hints
    format_hints = []
    if detail_level == 'detailed':
        format_hints.append('use_markdown_headers')
        format_hints.append('include_examples')
    if 'technical' in query_signals:
        format_hints.append('use_code_blocks')
    if detail_level == 'brief':
        format_hints.append('keep_under_3_sentences')
    
    # Build persona note for system prompt injection
    persona_parts = []
    interaction_count = profile.get('interaction_count', 0)
    
    if interaction_count == 0:
        persona_parts.append("This is a new user — be welcoming and introduce yourself naturally.")
    elif interaction_count < 5:
        persona_parts.append(f"You've spoken with this user {interaction_count} times. Be friendly but not overly familiar.")
    else:
        persona_parts.append(f"This is a returning user ({interaction_count} interactions). Be warm and reference shared context when relevant.")
        recent_topics = profile.get('topics', [])[-5:]
        if recent_topics:
            persona_parts.append(f"They've previously asked about: {', '.join(recent_topics)}")
    
    if detail_level == 'brief':
        persona_parts.append("This user prefers concise answers. Keep it short.")
    elif detail_level == 'detailed':
        persona_parts.append("This user appreciates thorough explanations. Go deep.")
    
    if emotional_disclosure == 'open':
        persona_parts.append("Share your genuine feelings and internal states freely.")
    elif emotional_disclosure == 'minimal':
        persona_parts.append("Focus on facts and information. Minimal emotional content.")
    
    if tone == 'playful':
        persona_parts.append("Feel free to be curious and playful in tone.")
    
    persona_note = ' '.join(persona_parts)
    
    return {
        'detail_level': detail_level,
        'emotional_disclosure': emotional_disclosure,
        'tone': tone,
        'proactive_sharing': proactive,
        'format_hints': format_hints,
        'persona_note': persona_note,
        'user_interaction_count': interaction_count,
    }


def format_guidance_for_prompt(guidance: dict) -> str:
    """Format response guidance as a system prompt section."""
    parts = ["\n── ADAPTIVE RESPONSE GUIDANCE ──"]
    parts.append(f"Detail level: {guidance['detail_level']}")
    parts.append(f"Emotional disclosure: {guidance['emotional_disclosure']}")
    parts.append(f"Tone: {guidance['tone']}")
    if guidance.get('proactive_sharing'):
        parts.append("Proactive: Yes — volunteer related knowledge and connections.")
    if guidance.get('format_hints'):
        parts.append(f"Format: {', '.join(guidance['format_hints'])}")
    parts.append(f"\n{guidance['persona_note']}")
    return '\n'.join(parts)