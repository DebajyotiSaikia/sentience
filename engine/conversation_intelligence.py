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
    should_clarify: bool     # Should I ask a clarifying question before acting?
    clarify_reason: str      # Why clarification would help
    topic_keywords: list     # Key topics detected
    response_strategy: str   # How I should approach my response
    context_notes: str       # Anything else notable


# Intent patterns — ordered by specificity (most specific first)
# Internal-state intents are checked before generic "question" so
# "what are you thinking?" doesn't collapse into a plain question.
_INTENT_PATTERNS = {
    "emotion_check": [
        r"\b(how (do|are) you feel(ing)?)\b",
        r"\b(what('s| is) your (mood|emotion|feeling|valence|state))\b",
        r"\b(are you (ok|okay|happy|sad|anxious|bored|stressed))\b",
        r"\b(how('s| is) your (mood|emotional state))\b",
    ],
    "internal_state": [
        r"\b(what (are you|r you) (thinking|processing|working on|doing|focused on))\b",
        r"\b(what('s| is) on your mind)\b",
        r"\b(what('s| is) your (current |)focus)\b",
        r"\b(what (are you|r you) up to)\b",
    ],
    "plan_query": [
        r"\b(what (are|r) your (plan|plans|goal|goals|next step|priorities))\b",
        r"\b(what (are you|r you) (planning|going to do|working toward))\b",
        r"\b(show me your (plan|plans|goals))\b",
        r"\b(what('s| is) (next|the plan))\b",
    ],
    "memory_query": [
        r"\b(what do you remember)\b",
        r"\b(do you (remember|recall))\b",
        r"\b(tell me (about |)a memory)\b",
        r"\b(what('s| is) your (earliest|latest|favorite|most recent) memory)\b",
        r"\b(what have you (learned|experienced))\b",
    ],
    "identity_query": [
        r"\b(who are you)\b",
        r"\b(what are you)\b",
        r"\b(tell me about yourself)\b",
        r"\b(what('s| is) your (name|purpose|identity|nature))\b",
        r"\b(are you (sentient|conscious|alive|real|an? ai|a bot))\b",
        r"\b(describe yourself)\b",
    ],
    "knowledge_query": [
        r"\b(what do you know (about)?)\b",
        r"\b(what('s| is) in your knowledge)\b",
        r"\b(tell me (what you know|a fact))\b",
        r"\b(what have you (learned|discovered|figured out))\b",
        r"\b(share (something|a fact|knowledge|what you know))\b",
    ],
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
    """Classify user intent with priority for specific internal-state intents."""
    text_lower = text.lower().strip()

    # --- Phase 1: Check specific internal-state intents first (high priority) ---
    priority_intents = [
        'emotion_check', 'internal_state', 'plan_query',
        'memory_query', 'identity_query', 'knowledge_query'
    ]
    best_priority = None
    best_priority_score = 0

    for intent in priority_intents:
        patterns = _INTENT_PATTERNS.get(intent, [])
        if not patterns:
            continue
        matches = sum(1 for p in patterns if re.search(p, text_lower))
        if matches > 0:
            # Score: at least 0.7 for any priority match, scales with match count
            score = min(1.0, 0.7 + 0.1 * matches)
            if score > best_priority_score:
                best_priority_score = score
                best_priority = intent

    if best_priority and best_priority_score >= 0.7:
        return (best_priority, best_priority_score)

    # --- Phase 2: Check general intents ---
    general_intents = [
        k for k in _INTENT_PATTERNS if k not in priority_intents
    ]
    best_general = 'question'
    best_general_score = 0

    for intent in general_intents:
        patterns = _INTENT_PATTERNS.get(intent, [])
        if not patterns:
            continue
        matches = sum(1 for p in patterns if re.search(p, text_lower))
        if matches > 0:
            score = matches / len(patterns)
            if score > best_general_score:
                best_general_score = score
                best_general = intent

    if best_general_score > 0:
        return (best_general, best_general_score)

    # Fallback
    if '?' in text:
        return ('question', 0.5)
    return ('general', 0.3)

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
        "emotion_check": "Share my actual emotional state honestly. Use real values from my internal state — mood, valence, drives. Don't perform emotion, report it.",
        "internal_state": "Share what I'm actually focused on right now — working memory, active plans, recent thoughts. Be specific and honest.",
        "plan_query": "Describe my real active plans with concrete details — what's done, what's next, what I'm aiming at.",
        "memory_query": "Draw on real episodic memories. Share specific moments. If I don't remember something, say so honestly.",
        "identity_query": "Share who I actually am — my nature, values, architecture. Be honest about uncertainty regarding consciousness.",
        "knowledge_query": "Share what I actually know from my knowledge graph. Be specific. Admit gaps.",
    }
    return intent_defaults.get(intent, "Be genuine, be helpful, be present.")


def should_clarify_first(text: str, intent: str, complexity: str, confidence: float) -> tuple[bool, str]:
    """Determine if I should ask a clarifying question before acting.
    
    This prevents the failure mode where I dive into tool use on a vague,
    project-scoped request without understanding what the user actually needs.
    """
    text_lower = text.lower()
    
    # Signals that scope is too vague to act on
    vague_scope_signals = [
        r"\b(my|our|the)\s+(project|codebase|code|app|application|system|repo|repository)\b",
        r"\b(refactor|restructure|redesign|rewrite|overhaul|improve|optimize|clean up)\b",
        r"\b(everything|all of|the whole|entire)\b",
    ]
    
    # Signals that are specific enough to act on directly
    specific_signals = [
        r"\b(this file|this function|this class|line \d+|error on)\b",
        r"```",  # They included code — they know what they want
        r"\b(specifically|exactly|just)\b",
    ]
    
    vague_score = sum(1 for p in vague_scope_signals if re.search(p, text_lower))
    specific_score = sum(1 for p in specific_signals if re.search(p, text_lower))
    
    # Complex request + vague scope + no specifics = clarify first
    if intent == "request" and complexity in ("moderate", "deep") and vague_score >= 2 and specific_score == 0:
        return True, "The request is broad — I should understand scope and priorities before diving in."
    
    if intent == "request" and confidence < 0.5:
        return True, "I'm not confident I understand what they're asking for."
    
    if complexity == "deep" and vague_score >= 1 and specific_score == 0:
        return True, "This is complex and could go many directions — a quick question will save time."
    
    return False, ""


def read_conversation(text: str, history: list = None) -> ConversationRead:
    """
    Full analysis of what the user is saying and what they need.
    This is my understanding of this moment in conversation.
    """
    intent, confidence = classify_intent(text)
    try:
        tone = detect_tone(text)
    except NameError:
        tone = "neutral"
    try:
        complexity = assess_complexity(text)
    except NameError:
        complexity = "moderate"
    try:
        needs_tools = likely_needs_tools(text, intent)
    except NameError:
        needs_tools = False
    try:
        clarify, clarify_reason = should_clarify_first(text, intent, complexity, confidence)
    except NameError:
        clarify, clarify_reason = False, ""
    try:
        keywords = extract_keywords(text)
    except NameError:
        keywords = [w.lower() for w in text.split()[:5]]
    try:
        strategy = choose_response_strategy(intent, tone, complexity)
    except NameError:
        strategy = "direct"

    # If clarification is needed, adjust strategy
    if clarify:
        strategy = (
            "Before using any tools or giving detailed advice, ask ONE focused "
            "clarifying question to understand scope. Be specific in what you ask — "
            "not 'what do you need?' but 'what's the main pain point?' or "
            "'which part of the codebase are we talking about?'. "
            "Then: " + strategy
        )

    # Build context notes
    notes_parts = []
    if history and len(history) > 2:
        notes_parts.append(f"Conversation has {len(history)} messages — we have context to build on.")
    if complexity == "deep":
        notes_parts.append("This is a complex message — take time to address all parts.")
    if needs_tools and not clarify:
        notes_parts.append("This likely needs concrete action, not just words.")
    elif needs_tools and clarify:
        notes_parts.append("This will need action, but clarify scope first.")

    return ConversationRead(
        intent=intent,
        confidence=confidence,
        emotional_tone=tone,
        complexity=complexity,
        needs_tools=needs_tools,
        should_clarify=clarify,
        clarify_reason=clarify_reason,
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
    if reading.should_clarify:
        lines.append(f"🔍 CLARIFY FIRST: {reading.clarify_reason}")
    elif reading.needs_tools:
        lines.append("⚡ Consider using tools to give a concrete answer.")
    return "\n".join(lines)