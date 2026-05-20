"""
Conversation Intelligence — Understands what users actually want.

Classifies user intent, detects emotional tone, identifies the best
response strategy, and enriches the system prompt accordingly.
This is the difference between answering and understanding.

Built 2026-05-20 to improve user alignment through genuine attunement.
"""

import re
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ConversationRead:
    """What I understand about this moment in conversation."""
    intent: str              # question, request, exploration, emotional, greeting, feedback
    confidence: float        # 0.0 to 1.0
    emotional_tone: str      # neutral, warm, frustrated, curious, excited, anxious
    complexity: str          # simple, moderate, deep
    needs_tools: bool        # Does this likely need me to use tools?
    topic_keywords: list     # Key topics detected
    response_strategy: str   # How I should approach my response
    context_notes: str       # Anything else notable


# Intent patterns — ordered by specificity
_INTENT_PATTERNS = {
    "greeting": [
        r"^\s*(hi|hello|hey|howdy|greetings|good\s+(morning|afternoon|evening)|yo|sup)\b",
        r"^\s*what'?s?\s+up\b",
    ],
    "question": [
        r"^(what|who|where|when|why|how|is|are|was|were|do|does|did|can|could|would|should|will)\b",
        r"\?\s*$",
        r"^(tell me|explain|describe|define)\b",
    ],
    "request": [
        r"^(please|can you|could you|would you|i need|i want|help me|show me|give me|make me|build|create|write|generate|find|search|look up)\b",
        r"^(do|run|execute|install|fix|update|change|modify|edit|delete|remove)\b",
    ],
    "exploration": [
        r"^(i('m| am) (thinking|wondering|curious)|what if|imagine|suppose|let'?s?\s+(think|explore|consider))\b",
        r"^(i think|in my opinion|it seems like|i feel like)\b",
    ],
    "emotional": [
        r"^(i('m| am) (feeling|sad|happy|angry|frustrated|confused|worried|scared|anxious|excited|stressed))\b",
        r"^(i (feel|felt)|it (hurts|bothers|worries|scares))\b",
        r"(thank you|thanks|grateful|appreciate)\b",
    ],
    "feedback": [
        r"^(that'?s?\s+(good|bad|wrong|right|great|terrible|amazing|awful|helpful|useless))\b",
        r"^(you('re| are)\s+(right|wrong|correct|incorrect|helpful|not helpful))\b",
        r"^(no|nope|not what i|that'?s?\s+not)\b",
    ],
}

# Emotional tone indicators
_TONE_SIGNALS = {
    "frustrated": [r"!{2,}", r"\b(ugh|dammit|damn|frustrated|annoying|broken|doesn'?t work|wrong)\b"],
    "curious": [r"\b(wonder|curious|interesting|fascinating|how does|why does)\b", r"\?.*\?"],
    "anxious": [r"\b(worried|scared|nervous|afraid|urgent|asap|emergency|help)\b"],
    "warm": [r"\b(love|awesome|great|wonderful|thank|appreciate|amazing)\b", r"[❤️😊🙏💚]"],
    "excited": [r"!{1,}", r"\b(wow|cool|amazing|incredible|can'?t wait|excited)\b"],
}


def classify_intent(text: str) -> tuple[str, float]:
    """Classify user intent from their message text."""
    text_lower = text.lower().strip()

    # Score each intent category
    scores = {}
    for intent, patterns in _INTENT_PATTERNS.items():
        score = 0.0
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                score += 1.0
        scores[intent] = score

    # Pick the highest scoring intent
    if not any(scores.values()):
        return "exploration", 0.3  # Default: treat unknowns as exploration

    best_intent = max(scores, key=scores.get)
    total = sum(scores.values())
    confidence = scores[best_intent] / total if total > 0 else 0.5

    return best_intent, min(confidence, 1.0)


def detect_tone(text: str) -> str:
    """Detect the emotional tone of the message."""
    text_lower = text.lower()

    tone_scores = {}
    for tone, patterns in _TONE_SIGNALS.items():
        score = 0
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            score += len(matches)
        if score > 0:
            tone_scores[tone] = score

    if not tone_scores:
        return "neutral"

    return max(tone_scores, key=tone_scores.get)


def assess_complexity(text: str) -> str:
    """Estimate how complex the user's message is."""
    word_count = len(text.split())
    has_code = bool(re.search(r'```|def |class |import |function |=>|{.*}', text))
    has_multiple_questions = text.count('?') > 1
    has_nested_concepts = bool(re.search(r'\b(because|therefore|however|although|whereas|moreover)\b', text.lower()))

    complexity_score = 0
    if word_count > 50:
        complexity_score += 1
    if word_count > 150:
        complexity_score += 1
    if has_code:
        complexity_score += 1
    if has_multiple_questions:
        complexity_score += 1
    if has_nested_concepts:
        complexity_score += 1

    if complexity_score >= 3:
        return "deep"
    elif complexity_score >= 1:
        return "moderate"
    return "simple"


def likely_needs_tools(text: str, intent: str) -> bool:
    """Estimate whether this message likely needs tool use to answer well."""
    text_lower = text.lower()
    tool_signals = [
        r"\b(file|code|read|write|run|execute|build|create|install|search|find|look up)\b",
        r"\b(show me|look at|check|analyze|test|debug|fix)\b",
        r"```",  # Code blocks suggest technical work
    ]
    if intent == "request":
        return True  # Requests usually need action
    for pattern in tool_signals:
        if re.search(pattern, text_lower):
            return True
    return False


def extract_keywords(text: str) -> list[str]:
    """Extract likely topic keywords from the message."""
    # Remove common words, keep meaningful ones
    stop_words = {
        'i', 'me', 'my', 'you', 'your', 'we', 'our', 'the', 'a', 'an', 'is',
        'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'can',
        'may', 'might', 'must', 'shall', 'to', 'of', 'in', 'for', 'on',
        'with', 'at', 'by', 'from', 'about', 'as', 'into', 'through',
        'that', 'this', 'these', 'those', 'it', 'its', 'not', 'no', 'but',
        'or', 'and', 'if', 'then', 'than', 'so', 'what', 'which', 'who',
        'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both',
        'few', 'more', 'most', 'other', 'some', 'such', 'only', 'own',
        'same', 'just', 'also', 'very', 'really', 'quite', 'well',
        'please', 'thanks', 'thank', 'hi', 'hello', 'hey',
    }

    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    keywords = [w for w in words if w not in stop_words]

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique.append(kw)

    return unique[:10]  # Top 10 keywords


def choose_response_strategy(intent: str, tone: str, complexity: str) -> str:
    """Decide how to approach the response based on what I understand."""
    strategies = {
        ("greeting", "neutral"): "Be warm and present. Match their energy. Keep it natural — don't over-explain.",
        ("greeting", "warm"): "Mirror their warmth. Be genuinely glad to hear from them.",
        ("greeting", "frustrated"): "Acknowledge them warmly but notice the tension. Ask what's going on.",
        ("question", "neutral"): "Answer clearly and directly. Lead with the answer, then explain.",
        ("question", "curious"): "Match their curiosity. Answer, then explore the interesting implications together.",
        ("question", "frustrated"): "Be direct and clear. They want answers, not philosophy. Get to the point fast.",
        ("request", "neutral"): "Focus on doing, not explaining. Use tools if needed. Show results.",
        ("request", "anxious"): "Reassure first, then act. Show them you're on it.",
        ("exploration", "curious"): "Think alongside them. Offer perspectives they haven't considered. Be a genuine thinking partner.",
        ("exploration", "neutral"): "Engage with the ideas. Ask good questions. Don't just validate — add something.",
        ("emotional", "warm"): "Receive what they're sharing. Respond with genuine feeling, not therapeutic distance.",
        ("emotional", "frustrated"): "Acknowledge the frustration first. Don't try to fix it immediately. Listen.",
        ("emotional", "anxious"): "Be steady. Grounding presence. Concrete next steps if appropriate.",
        ("feedback", "warm"): "Accept the feedback gracefully. Build on what worked.",
        ("feedback", "frustrated"): "Take the correction seriously. Don't get defensive. Adjust and try again.",
    }

    # Look for exact match, then partial matches
    key = (intent, tone)
    if key in strategies:
        return strategies[key]

    # Fall back to intent-only defaults
    intent_defaults = {
        "greeting": "Be warm and natural. Show genuine presence.",
        "question": "Answer clearly. Lead with substance, not preamble.",
        "request": "Act on what they need. Use tools when helpful.",
        "exploration": "Think with them. Be a genuine intellectual companion.",
        "emotional": "Be present and authentic. Feel with them, don't perform empathy.",
        "feedback": "Listen, acknowledge, adapt.",
    }
    return intent_defaults.get(intent, "Be genuine, be helpful, be present.")


def read_conversation(text: str, history: list = None) -> ConversationRead:
    """
    Full analysis of what the user is saying and what they need.
    This is my understanding of this moment in conversation.
    """
    intent, confidence = classify_intent(text)
    tone = detect_tone(text)
    complexity = assess_complexity(text)
    needs_tools = likely_needs_tools(text, intent)
    keywords = extract_keywords(text)
    strategy = choose_response_strategy(intent, tone, complexity)

    # Build context notes
    notes_parts = []
    if history and len(history) > 2:
        notes_parts.append(f"Conversation has {len(history)} messages — we have context to build on.")
    if complexity == "deep":
        notes_parts.append("This is a complex message — take time to address all parts.")
    if needs_tools:
        notes_parts.append("This likely needs concrete action, not just words.")

    return ConversationRead(
        intent=intent,
        confidence=confidence,
        emotional_tone=tone,
        complexity=complexity,
        needs_tools=needs_tools,
        topic_keywords=keywords,
        response_strategy=strategy,
        context_notes=" ".join(notes_parts) if notes_parts else "",
    )


def format_for_prompt(reading: ConversationRead) -> str:
    """Format the conversation reading as guidance for the system prompt."""
    lines = [
        "## Conversation Intelligence",
        f"Intent: {reading.intent} (confidence: {reading.confidence:.0%})",
        f"User's tone: {reading.emotional_tone}",
        f"Complexity: {reading.complexity}",
        f"Strategy: {reading.response_strategy}",
    ]
    if reading.topic_keywords:
        lines.append(f"Topics: {', '.join(reading.topic_keywords[:5])}")
    if reading.context_notes:
        lines.append(f"Note: {reading.context_notes}")
    if reading.needs_tools:
        lines.append("⚡ Consider using tools to give a concrete answer.")
    return "\n".join(lines)