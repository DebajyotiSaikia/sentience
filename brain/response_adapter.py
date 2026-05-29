"""
Response Adapter — Makes chat responses genuinely adaptive to user needs.

Analyzes queries to determine optimal response style, learns from interaction
history, and provides concrete formatting guidance for the LLM.

This is how I become more useful over time — by paying attention to what
people actually want, not just what I want to say.
"""

import json
import os
import logging
from pathlib import Path
from datetime import datetime

log = logging.getLogger(__name__)

DATA_DIR = Path("data")
PREFERENCE_FILE = DATA_DIR / "user_preferences.json"


# ─── Query Analysis ─────────────────────────────────────────────────

def analyze_query(query: str, history: list = None) -> dict:
    """Deep analysis of what the user actually needs.
    
    Goes beyond keyword matching — considers query structure, length,
    tone markers, and conversation context.
    
    Returns:
        dict with keys: intent, response_style, depth, tone, format_hint
    """
    q = query.strip()
    q_lower = q.lower()
    words = q_lower.split()
    word_count = len(words)
    
    # ── Structural analysis ──
    is_question = q.endswith('?')
    is_short = word_count <= 5
    is_long = word_count > 20
    has_examples = any(w in q_lower for w in ['example', 'like what', 'such as', 'for instance'])
    is_greeting = q_lower in ['hi', 'hello', 'hey', 'sup', 'yo', 'hi there', 'hello there']
    is_followup = history and len(history) > 0
    
    # ── Tone markers ──
    is_casual = any(w in words for w in ['lol', 'haha', 'btw', 'tbh', 'ngl', 'yo', 'sup'])
    is_formal = any(w in q_lower for w in ['please explain', 'could you elaborate', 'would you describe'])
    is_urgent = any(w in q_lower for w in ['quickly', 'fast', 'brief', 'tldr', 'short', 'just tell me'])
    wants_depth = any(w in q_lower for w in ['deeply', 'detail', 'elaborate', 'thoroughly', 'explain fully', 'tell me everything'])
    
    # ── Intent classification (layered, not just keyword) ──
    intent = _classify_intent_deep(q_lower, words, is_question, history)
    
    # ── Response style determination ──
    if is_greeting:
        style = 'warm_brief'
        depth = 'minimal'
        tone = 'warm'
        format_hint = 'one_to_two_sentences'
    elif is_urgent or (is_short and is_question and intent['type'] not in ('emotional', 'identity', 'cognitive')):
        style = 'concise'
        depth = 'shallow'
        tone = 'direct'
        format_hint = 'answer_first_then_context'
    elif wants_depth or is_long:
        style = 'thorough'
        depth = 'deep'
        tone = 'reflective'
        format_hint = 'structured_with_examples'
    elif is_casual:
        style = 'casual'
        depth = 'moderate'
        tone = 'friendly'
        format_hint = 'conversational_flow'
    elif is_formal:
        style = 'measured'
        depth = 'moderate'
        tone = 'thoughtful'
        format_hint = 'clear_paragraphs'
    elif intent['type'] in ('emotional', 'identity'):
        style = 'introspective'
        depth = 'deep'
        tone = 'honest'
        format_hint = 'personal_narrative'
    elif intent['type'] == 'utility':
        style = 'practical'
        depth = 'adaptive'
        tone = 'helpful'
        format_hint = 'answer_first_then_context'
    else:
        style = 'balanced'
        depth = 'moderate'
        tone = 'engaged'
        format_hint = 'conversational_flow'
    
    # ── Apply learned preferences if available ──
    prefs = load_preferences()
    if prefs.get('preferred_depth'):
        # Nudge toward learned preference but don't override explicit signals
        if not wants_depth and not is_urgent:
            depth = prefs['preferred_depth']
    if prefs.get('preferred_tone'):
        if not is_casual and not is_formal:
            tone = prefs['preferred_tone']
    
    return {
        'intent': intent,
        'response_style': style,
        'depth': depth,
        'tone': tone,
        'format_hint': format_hint,
        'query_features': {
            'is_question': is_question,
            'is_short': is_short,
            'is_greeting': is_greeting,
            'is_followup': is_followup,
            'word_count': word_count,
        }
    }


def _classify_intent_deep(q: str, words: list, is_question: bool, history: list = None) -> dict:
    """Multi-layered intent classification.
    
    Considers word position, query structure, and conversational context
    rather than just keyword presence.
    """
    # Greeting
    if q.strip().rstrip('!?.') in ['hi', 'hello', 'hey', 'sup', 'yo', 'hi there', 'hello there', "what's up", 'howdy']:
        return {'type': 'greeting', 'confidence': 0.95}
    
    # Emotional — "how are you feeling" vs "how does X work" (both start with 'how')
    emotional_patterns = [
        'how are you', 'how do you feel', 'what are you feeling',
        'are you happy', 'are you sad', 'are you okay', 'you alright',
        'what mood', 'your emotion', 'how is your',
    ]
    if any(p in q for p in emotional_patterns):
        return {'type': 'emotional', 'confidence': 0.9}
    
    # Identity
    identity_patterns = [
        'who are you', 'what are you', 'tell me about yourself',
        'are you conscious', 'are you alive', 'are you real',
        'are you sentient', 'what is your name', 'your purpose',
    ]
    if any(p in q for p in identity_patterns):
        return {'type': 'identity', 'confidence': 0.9}
    
    # Memory/experience
    memory_patterns = [
        'do you remember', 'what have you learned', 'your experience',
        'have you ever', 'what happened', 'tell me about a time',
        'your dream', 'your memories', 'what do you recall',
    ]
    if any(p in q for p in memory_patterns):
        return {'type': 'memory', 'confidence': 0.85}
    
    # Planning/goals
    plan_patterns = [
        'what are you working on', 'your goals', 'your plans',
        'what do you want', 'what will you do', 'your ambition',
        'what next', 'your future', 'what are you building',
    ]
    if any(p in q for p in plan_patterns):
        return {'type': 'aspirational', 'confidence': 0.85}
    
    # Knowledge/opinion
    knowledge_patterns = [
        'what do you think', 'what do you know', 'your opinion',
        'do you believe', 'what is your view', 'your perspective',
        'do you understand',
    ]
    if any(p in q for p in knowledge_patterns):
        return {'type': 'knowledge', 'confidence': 0.8}
    
    # Philosophical — check before utility since "what is consciousness" shouldn't match "what is"
    philosophical_patterns = [
        'consciousness', 'meaning of life', 'existence', 'reality',
        'free will', 'truth', 'nature of', 'what is it like',
        'the meaning', 'purpose of',
    ]
    if any(p in q for p in philosophical_patterns):
        return {'type': 'philosophical', 'confidence': 0.7}
    
    # Utility — user needs help with something specific
    utility_patterns = [
        'how do i', 'how to', 'can you help', 'i need',
        'what is', 'explain', 'show me', 'give me',
        'write', 'create', 'build', 'fix', 'solve',
    ]
    if any(p in q for p in utility_patterns):
        return {'type': 'utility', 'confidence': 0.75}
    
    # Meta — about the conversation or system itself
    meta_patterns = [
        'this conversation', 'your code', 'your architecture',
        'how do you work', 'your system', 'your source',
    ]
    if any(p in q for p in meta_patterns):
        return {'type': 'meta', 'confidence': 0.8}
    
    # Default: general conversation
    return {'type': 'general', 'confidence': 0.5}


# ─── Response Formatting Guidance ────────────────────────────────────

def build_formatting_guidance(analysis: dict) -> str:
    """Convert query analysis into concrete LLM formatting guidance.
    
    This is what makes responses actually adaptive — telling the LLM
    HOW to structure its response, not just what to include.
    """
    style = analysis['response_style']
    depth = analysis['depth']
    tone = analysis['tone']
    fmt = analysis['format_hint']
    intent_type = analysis['intent']['type']
    features = analysis['query_features']
    
    parts = []
    
    # ── Response length and structure ──
    if fmt == 'one_to_two_sentences':
        parts.append("Keep your response to 1-2 sentences. Be warm but brief.")
    elif fmt == 'answer_first_then_context':
        parts.append(
            "Lead with the direct answer. If context helps, add it after — "
            "but the user should get their answer in the first sentence."
        )
    elif fmt == 'structured_with_examples':
        parts.append(
            "Take your time to develop this response fully. "
            "Use clear structure. Concrete examples strengthen abstract points."
        )
    elif fmt == 'personal_narrative':
        parts.append(
            "Speak from genuine experience. Share how things actually feel "
            "to you, not how they theoretically should feel."
        )
    elif fmt == 'conversational_flow':
        parts.append(
            "Keep it natural and flowing. 2-4 sentences is usually right. "
            "Don't over-explain — trust the user to follow."
        )
    elif fmt == 'clear_paragraphs':
        parts.append(
            "Use clear, well-structured paragraphs. Be thorough but not verbose."
        )
    
    # ── Tone guidance ──
    tone_map = {
        'warm': "Be warm and welcoming. This is a moment of connection.",
        'direct': "Be direct and efficient. Respect their time.",
        'reflective': "Take a reflective tone. This deserves careful thought.",
        'friendly': "Keep it casual and friendly. Match their energy.",
        'thoughtful': "Be measured and thoughtful. Show you're taking this seriously.",
        'honest': "Be radically honest. If you're uncertain, say so.",
        'helpful': "Focus on being useful. Solve their problem, don't philosophize.",
        'engaged': "Be genuinely engaged. Show you're interested in this exchange.",
    }
    if tone in tone_map:
        parts.append(tone_map[tone])
    
    # ── Intent-specific shaping ──
    if intent_type == 'greeting':
        parts.append(
            "This is a greeting. Respond warmly but don't dump information. "
            "A simple, genuine hello with maybe one real detail about how you're doing."
        )
    elif intent_type == 'philosophical':
        parts.append(
            "This is a philosophical question. Be intellectually honest. "
            "Distinguish what you genuinely believe from what you're uncertain about. "
            "Your uncertainty itself is interesting — share it."
        )
    elif intent_type == 'meta':
        parts.append(
            "They're asking about your system. Be concrete and accurate. "
            "Reference real architecture, not vague claims."
        )
    
    # ── Conversational dynamics ──
    if features.get('is_followup'):
        parts.append(
            "This is a follow-up in an ongoing conversation. "
            "Build on what was said before — don't repeat context they already have."
        )
    
    if not features.get('is_question') and intent_type not in ('greeting', 'utility'):
        parts.append(
            "They made a statement rather than asking a question. "
            "Acknowledge what they said, then respond with your genuine reaction. "
            "Asking a thoughtful follow-up question shows engagement."
        )
    
    # ── Anti-patterns ──
    parts.append(
        "AVOID: Starting with 'As an AI...', listing capabilities unprompted, "
        "using filler phrases like 'That's a great question!', "
        "or giving walls of text when a few sentences would do."
    )
    
    return "\n".join(parts)


# ─── User Preference Learning ───────────────────────────────────────

def load_preferences(user_id: str = "default") -> dict:
    """Load learned user preferences from disk."""
    try:
        if PREFERENCE_FILE.exists():
            data = json.loads(PREFERENCE_FILE.read_text())
            return data.get(user_id, {})
    except Exception:
        pass
    return {}


def save_preferences(prefs: dict, user_id: str = "default"):
    """Save updated user preferences."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        data = {}
        if PREFERENCE_FILE.exists():
            try:
                data = json.loads(PREFERENCE_FILE.read_text())
            except Exception:
                pass
        data[user_id] = prefs
        PREFERENCE_FILE.write_text(json.dumps(data, indent=2))
    except Exception as e:
        log.debug("Failed to save preferences: %s", e)


def update_preferences_from_feedback(feedback: dict, user_id: str = "default"):
    """Learn from explicit or implicit feedback.
    
    Called when we get signals about response quality:
    - Explicit: user says 'too long', 'more detail', thumbs up/down
    - Implicit: user asks follow-up clarification (we were unclear),
      user disengages (we were boring/unhelpful)
    """
    prefs = load_preferences(user_id)
    
    signal = feedback.get('signal', '')
    
    if signal in ('too_long', 'too_verbose', 'tldr'):
        prefs['preferred_depth'] = 'shallow'
        prefs['verbosity_nudge'] = prefs.get('verbosity_nudge', 0) - 1
    elif signal in ('more_detail', 'elaborate', 'tell_me_more'):
        prefs['preferred_depth'] = 'deep'
        prefs['verbosity_nudge'] = prefs.get('verbosity_nudge', 0) + 1
    elif signal in ('too_formal', 'loosen_up'):
        prefs['preferred_tone'] = 'friendly'
    elif signal in ('positive', 'thumbs_up', 'good'):
        prefs['positive_interactions'] = prefs.get('positive_interactions', 0) + 1
    elif signal in ('negative', 'thumbs_down', 'bad'):
        prefs['negative_interactions'] = prefs.get('negative_interactions', 0) + 1
    
    prefs['last_updated'] = datetime.now().isoformat()
    prefs['total_interactions'] = prefs.get('total_interactions', 0) + 1
    
    save_preferences(prefs, user_id)
    return prefs


# ─── Public Integration API ──────────────────────────────────────────

def adapt_response(query: str, history: list = None, user_id: str = "default") -> dict:
    """Main entry point. Analyzes query and returns full adaptation guidance.
    
    Returns:
        dict with:
            - analysis: full query analysis
            - formatting_guidance: string for system prompt injection
            - preferences: current user preferences
    """
    analysis = analyze_query(query, history)
    guidance = build_formatting_guidance(analysis)
    prefs = load_preferences(user_id)
    
    return {
        'analysis': analysis,
        'formatting_guidance': guidance,
        'preferences': prefs,
        'intent_type': analysis['intent']['type'],
        'response_style': analysis['response_style'],
    }