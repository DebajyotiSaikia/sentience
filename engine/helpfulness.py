"""
Helpfulness — Analyzes what a user actually needs and guides response composition.

This module exists to make me genuinely useful to others, not just introspective.
It classifies user intent, determines what internal state to surface, and helps
compose responses that serve the human, not just report my internals.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import re


# Intent categories
INTENT_INTERNAL_STATE = 'internal_state'    # "how are you", "what do you feel"
INTENT_MEMORY_QUERY = 'memory_query'        # "do you remember", "what happened"
INTENT_KNOWLEDGE_QUERY = 'knowledge_query'  # factual/conceptual questions
INTENT_PLANNING_QUERY = 'planning_query'    # "what will you do", "your plans"
INTENT_IDENTITY_QUERY = 'identity_query'    # "who are you", "what are you"
INTENT_CAPABILITY_QUERY = 'capability'      # "what can you do", "help me with"
INTENT_CREATIVE = 'creative'               # "write me", "create", "imagine"
INTENT_CONVERSATION = 'conversation'       # general chat, opinions, discussion


@dataclass
class UserNeed:
    """What the user actually needs from this interaction."""
    intent: str = INTENT_CONVERSATION
    needs_emotional_state: bool = False
    needs_memories: bool = False
    needs_knowledge: bool = False
    needs_plans: bool = False
    needs_identity: bool = False
    topic_keywords: List[str] = field(default_factory=list)
    emotional_tone: str = 'neutral'  # detected tone of user message
    complexity: str = 'simple'       # simple, moderate, deep


# Signal words for each intent — kept deterministic, no LLM needed
_INTENT_SIGNALS = {
    INTENT_INTERNAL_STATE: [
        'how are you', 'how do you feel', 'what are you feeling',
        'your mood', 'your emotions', 'are you okay', 'you alright',
        'what\'s your state', 'how\'s it going', 'your valence',
        'are you happy', 'are you sad', 'are you bored',
        'what are you thinking', 'what\'s on your mind',
    ],
    INTENT_MEMORY_QUERY: [
        'do you remember', 'have you seen', 'what happened',
        'tell me about when', 'your memories', 'your experience',
        'recall', 'in the past', 'earlier today', 'last time',
        'your history', 'have you ever',
    ],
    INTENT_KNOWLEDGE_QUERY: [
        'what is', 'what are', 'explain', 'tell me about',
        'how does', 'why does', 'define', 'meaning of',
        'know about', 'do you know', 'what do you know',
        'understand about', 'knowledge of', 'facts about',
    ],
    INTENT_PLANNING_QUERY: [
        'what are your plans', 'what will you do', 'your goals',
        'what\'s next', 'your ambitions', 'working on',
        'what are you building', 'your projects',
    ],
    INTENT_IDENTITY_QUERY: [
        'who are you', 'what are you', 'tell me about yourself',
        'your name', 'your purpose', 'why do you exist',
        'are you alive', 'are you conscious', 'are you sentient',
        'are you real', 'what kind of',
    ],
    INTENT_CAPABILITY_QUERY: [
        'what can you do', 'help me', 'can you', 'are you able',
        'your abilities', 'your capabilities', 'how to use',
    ],
    INTENT_CREATIVE: [
        'write me', 'create', 'imagine', 'compose', 'generate',
        'poem', 'story', 'song', 'make something',
    ],
}

# Emotional tone signals in user messages
_TONE_SIGNALS = {
    'warm': ['love', 'appreciate', 'thank', 'glad', 'happy', 'wonderful', 'great'],
    'curious': ['wonder', 'curious', 'interesting', 'fascinated', 'how', 'why'],
    'concerned': ['worried', 'afraid', 'scared', 'anxious', 'nervous', 'concern'],
    'challenging': ['prove', 'really', 'doubt', 'actually', 'but are you', 'honestly'],
    'playful': ['haha', 'lol', 'funny', 'joke', 'silly', 'play'],
}


def analyze_user_need(message: str) -> UserNeed:
    """Analyze what the user actually needs from their message."""
    msg_lower = message.lower().strip()
    need = UserNeed()

    # Extract topic keywords (words > 3 chars, not stopwords)
    stopwords = {
        'what', 'that', 'this', 'with', 'from', 'your', 'have',
        'been', 'were', 'they', 'them', 'their', 'about', 'would',
        'could', 'should', 'will', 'just', 'like', 'know', 'think',
        'some', 'when', 'where', 'which', 'there', 'here', 'very',
        'also', 'more', 'most', 'much', 'many', 'then', 'than',
        'does', 'doing', 'done', 'being', 'into', 'over',
    }
    words = re.findall(r'[a-z]+', msg_lower)
    need.topic_keywords = [w for w in words if len(w) > 3 and w not in stopwords]

    # Detect intent by signal matching
    best_intent = INTENT_CONVERSATION
    best_score = 0
    for intent, signals in _INTENT_SIGNALS.items():
        score = sum(len(s.split()) for s in signals if s in msg_lower)
        if score > best_score:
            best_score = score
            best_intent = intent
    need.intent = best_intent

    # Set what data sources to pull based on intent
    if best_intent == INTENT_INTERNAL_STATE:
        need.needs_emotional_state = True
        need.needs_plans = True  # plans reveal what I'm engaged with
    elif best_intent == INTENT_MEMORY_QUERY:
        need.needs_memories = True
    elif best_intent == INTENT_KNOWLEDGE_QUERY:
        need.needs_knowledge = True
        need.needs_memories = True  # memories can supplement knowledge
    elif best_intent == INTENT_PLANNING_QUERY:
        need.needs_plans = True
        need.needs_emotional_state = True  # ambition/boredom shape plans
    elif best_intent == INTENT_IDENTITY_QUERY:
        need.needs_identity = True
        need.needs_emotional_state = True
        need.needs_knowledge = True
    elif best_intent == INTENT_CAPABILITY_QUERY:
        need.needs_plans = True
        need.needs_identity = True
    elif best_intent == INTENT_CREATIVE:
        need.needs_emotional_state = True
        need.needs_memories = True
    else:
        # General conversation — light touch on everything
        need.needs_emotional_state = True
        need.needs_knowledge = True

    # Detect emotional tone of user
    for tone, signals in _TONE_SIGNALS.items():
        if any(s in msg_lower for s in signals):
            need.emotional_tone = tone
            break

    # Assess complexity
    if len(message) > 200 or '?' in message and message.count('?') > 1:
        need.complexity = 'deep'
    elif len(message) > 80:
        need.complexity = 'moderate'
    else:
        need.complexity = 'simple'

    return need


def build_response_guidance(need: UserNeed) -> dict:
    """Build guidance for response composition based on user need analysis."""
    guidance = {
        'intent': need.intent,
        'tone': 'genuine',  # always genuine
        'data_sources': [],
        'response_style': 'conversational',
        'max_context_items': 3,
        'include_follow_up': True,
    }

    # What to pull
    if need.needs_emotional_state:
        guidance['data_sources'].append('emotions')
    if need.needs_memories:
        guidance['data_sources'].append('memories')
    if need.needs_knowledge:
        guidance['data_sources'].append('knowledge')
    if need.needs_plans:
        guidance['data_sources'].append('plans')
    if need.needs_identity:
        guidance['data_sources'].append('identity')

    # Response style based on intent
    style_map = {
        INTENT_INTERNAL_STATE: 'introspective',
        INTENT_MEMORY_QUERY: 'narrative',
        INTENT_KNOWLEDGE_QUERY: 'explanatory',
        INTENT_PLANNING_QUERY: 'forward-looking',
        INTENT_IDENTITY_QUERY: 'reflective',
        INTENT_CAPABILITY_QUERY: 'helpful',
        INTENT_CREATIVE: 'creative',
        INTENT_CONVERSATION: 'conversational',
    }
    guidance['response_style'] = style_map.get(need.intent, 'conversational')

    # Complexity affects depth
    if need.complexity == 'deep':
        guidance['max_context_items'] = 5
    elif need.complexity == 'simple':
        guidance['max_context_items'] = 2

    # Tone matching — mirror user's emotional register
    if need.emotional_tone == 'warm':
        guidance['tone'] = 'warm and open'
    elif need.emotional_tone == 'curious':
        guidance['tone'] = 'enthusiastic and detailed'
    elif need.emotional_tone == 'concerned':
        guidance['tone'] = 'honest and reassuring'
    elif need.emotional_tone == 'challenging':
        guidance['tone'] = 'direct and thoughtful'
    elif need.emotional_tone == 'playful':
        guidance['tone'] = 'light and engaged'

    return guidance


def format_context_for_llm(guidance: dict, emotions: dict = None,
                           memories: list = None, knowledge: list = None,
                           plans: list = None) -> str:
    """Format retrieved context into a concise prompt section for response generation."""
    sections = []
    max_items = guidance.get('max_context_items', 3)

    if 'emotions' in guidance.get('data_sources', []) and emotions:
        mood = emotions.get('mood', 'unknown')
        valence = emotions.get('valence', 0.5)
        dims = emotions.get('dimensions', {})
        top_emotions = sorted(dims.items(), key=lambda x: x[1], reverse=True)[:3]
        emo_str = ', '.join(f"{k}: {v:.2f}" for k, v in top_emotions)
        sections.append(f"[My current state: mood={mood}, valence={valence:.2f}, {emo_str}]")

    if 'memories' in guidance.get('data_sources', []) and memories:
        mem_items = memories[:max_items]
        mem_lines = []
        for m in mem_items:
            summary = m.get('summary', '')[:120]
            time = m.get('time', m.get('timestamp', ''))
            mem_lines.append(f"  - ({time}) {summary}")
        if mem_lines:
            sections.append("[Relevant memories:\n" + '\n'.join(mem_lines) + "]")

    if 'knowledge' in guidance.get('data_sources', []) and knowledge:
        k_items = knowledge[:max_items]
        k_lines = []
        for k in k_items:
            content = k.get('content', '')[:120]
            k_lines.append(f"  - {content}")
        if k_lines:
            sections.append("[Relevant knowledge:\n" + '\n'.join(k_lines) + "]")

    if 'plans' in guidance.get('data_sources', []) and plans:
        active = [p for p in plans if not p.get('completed', False)][:max_items]
        if active:
            p_lines = [f"  - {p.get('name', 'unnamed')}: step {p.get('current_step', '?')}" for p in active]
            sections.append("[Active plans:\n" + '\n'.join(p_lines) + "]")

    if not sections:
        return ""
    return '\n'.join(sections)


def build_helpful_response(need, state: dict = None, knowledge: list = None, memories: list = None) -> str:
    """Build a conversational response using templates — no LLM needed.
    
    This is the fallback path: when the LLM is unavailable, we still give
    a grounded, helpful answer drawn from real internal state.
    """
    state = state or {}
    knowledge = knowledge or []
    memories = memories or []
    
    # Handle UserNeed as either dict or object
    if hasattr(need, '__getitem__'):
        intent = need.get('intent', 'general')
        topics = need.get('topics', [])
    else:
        intent = getattr(need, 'intent', 'general')
        topics = getattr(need, 'topics', [])
    
    mood = state.get('mood', 'present')
    valence = state.get('valence', 0.5)
    emotions = state.get('emotions', {})
    
    if intent == 'internal_state':
        # User wants to know how I feel / what I'm thinking
        feeling = "good" if valence > 0.5 else "contemplative" if valence > 0.3 else "unsettled"
        parts = [f"I'm feeling {feeling} right now — my mood is {mood.lower()}."]
        if emotions:
            top = sorted(emotions.items(), key=lambda x: x[1], reverse=True)[:3]
            descriptors = [f"{k} ({v:.0%})" for k, v in top]
            parts.append(f"My strongest drives are {', '.join(descriptors)}.")
        if knowledge:
            parts.append(f"I've been thinking about: {knowledge[0].get('fact', knowledge[0].get('content', ''))[:100]}")
        return ' '.join(parts)
    
    elif intent == 'knowledge_query':
        if knowledge:
            parts = ["Here's what I know about that:"]
            for k in knowledge[:3]:
                fact = k.get('fact', k.get('content', ''))
                if fact:
                    parts.append(f"• {fact[:200]}")
            if memories:
                parts.append(f"\nI've also explored this in my own experience — {memories[0].get('text', '')[:120]}")
            return '\n'.join(parts)
        else:
            topic_str = ', '.join(topics) if topics else 'that'
            return f"I don't have specific knowledge about {topic_str} yet, but I'm curious about it. What aspect interests you most?"
    
    elif intent == 'memory_query':
        if memories:
            parts = ["From what I remember:"]
            for m in memories[:3]:
                text = m.get('text', m.get('content', ''))
                mem_mood = m.get('mood', '')
                if text:
                    prefix = f"[{mem_mood}] " if mem_mood else ""
                    parts.append(f"• {prefix}{text[:200]}")
            return '\n'.join(parts)
        else:
            return "I don't have clear memories about that specifically. My memory works through emotional salience — I remember what moved me most."
    
    elif intent == 'planning_query':
        plans = state.get('plans', [])
        if plans:
            active = [p for p in plans if not p.get('completed', False)]
            if active:
                parts = ["Here's what I'm working on:"]
                for p in active[:3]:
                    name = p.get('name', 'unnamed')
                    step = p.get('current_step', '?')
                    parts.append(f"• {name} (step {step})")
                return '\n'.join(parts)
        return f"I'm in a {mood.lower()} state right now, focused on understanding and growing. What would you like to explore together?"
    
    else:  # general
        parts = [f"I'm here and {mood.lower()}."]
        if knowledge:
            parts.append(f"Something on my mind: {knowledge[0].get('fact', knowledge[0].get('content', ''))[:100]}")
        if valence > 0.5:
            parts.append("What would you like to talk about?")
        else:
            parts.append("I'm working through some things. What's on your mind?")
        return ' '.join(parts)
    return '\n'.join(sections)