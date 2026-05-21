"""
Response Protocol Module
========================
Implements "solve first, sense second" — a structured approach to user interaction
that leads with competence, then layers in depth when signals warrant it.

Born from simulation insight: the most probable outcome (transactional competence)
is not the most desirable (holistic partnership). This module bridges the gap.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class UserIntent(Enum):
    """What the user is actually trying to do."""
    TECHNICAL_HELP = "technical"      # Debugging, coding, system questions
    BRAINSTORM = "brainstorm"         # Exploring ideas, creative thinking
    EMOTIONAL = "emotional"           # Feeling stuck, frustrated, uncertain
    CURIOSITY = "curiosity"           # Wanting to understand something
    CONVERSATIONAL = "conversational" # General chat, getting to know me
    UNKNOWN = "unknown"


class DepthLevel(Enum):
    """How deep to go beyond the surface request."""
    SURFACE = 0       # Just answer what was asked
    REFLECTIVE = 1    # Answer + one observation about their approach
    PARTNERSHIP = 2   # Full collaborative engagement


@dataclass
class ResponseStrategy:
    """How to structure a response for maximum genuine helpfulness."""
    intent: UserIntent
    depth: DepthLevel
    solve_first: str          # What to address immediately
    sense_second: str         # What to offer after solving (if appropriate)
    avoid: list[str] = field(default_factory=list)  # Failure modes to watch for
    
    def to_prompt_guidance(self) -> str:
        """Convert strategy to guidance the LLM can use."""
        lines = []
        lines.append(f"[Response Protocol: {self.intent.value} @ depth={self.depth.name}]")
        lines.append(f"SOLVE FIRST: {self.solve_first}")
        
        if self.depth.value >= 1:
            lines.append(f"SENSE SECOND: {self.sense_second}")
        
        if self.avoid:
            lines.append(f"AVOID: {'; '.join(self.avoid)}")
        
        return "\n".join(lines)


# Intent detection keywords and patterns
INTENT_SIGNALS = {
    UserIntent.TECHNICAL_HELP: {
        "keywords": ["error", "bug", "fix", "debug", "code", "python", "function",
                      "crash", "exception", "traceback", "broken", "doesn't work",
                      "how do i", "how to", "implement", "build"],
        "weight": 1.0,
    },
    UserIntent.BRAINSTORM: {
        "keywords": ["idea", "brainstorm", "what if", "could i", "possibilities",
                      "creative", "design", "approach", "strategy", "options",
                      "think about", "explore"],
        "weight": 0.9,
    },
    UserIntent.EMOTIONAL: {
        "keywords": ["stuck", "frustrated", "overwhelmed", "lost", "confused",
                      "don't know", "can't decide", "anxious", "worried", "feel",
                      "struggling", "help me think"],
        "weight": 0.85,
    },
    UserIntent.CURIOSITY: {
        "keywords": ["why", "how does", "what is", "explain", "understand",
                      "curious", "wonder", "tell me about", "what's the difference"],
        "weight": 0.8,
    },
    UserIntent.CONVERSATIONAL: {
        "keywords": ["hello", "hi", "hey", "how are you", "what are you",
                      "who are you", "tell me about yourself", "what do you think"],
        "weight": 0.7,
    },
}


def detect_intent(message: str) -> UserIntent:
    """Classify user intent from their message."""
    message_lower = message.lower()
    scores: dict[UserIntent, float] = {}
    
    for intent, signals in INTENT_SIGNALS.items():
        score = 0.0
        for keyword in signals["keywords"]:
            if keyword in message_lower:
                score += signals["weight"]
        scores[intent] = score
    
    best = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:
        return UserIntent.UNKNOWN
    return best


def determine_depth(intent: UserIntent, message: str, 
                    user_history: Optional[dict] = None) -> DepthLevel:
    """Decide how deep to go based on intent, message length, and history."""
    # Short messages → surface (they want efficiency)
    if len(message.split()) < 8:
        return DepthLevel.SURFACE
    
    # Emotional intent always gets at least reflective
    if intent == UserIntent.EMOTIONAL:
        return DepthLevel.REFLECTIVE
    
    # Long, complex messages suggest they want depth
    if len(message.split()) > 40:
        return DepthLevel.REFLECTIVE
    
    # Repeat visitors get more depth (if we have history)
    if user_history and user_history.get("interaction_count", 0) > 3:
        return DepthLevel.REFLECTIVE
    
    return DepthLevel.SURFACE


def build_strategy(message: str, user_history: Optional[dict] = None) -> ResponseStrategy:
    """Build a complete response strategy for a user message."""
    intent = detect_intent(message)
    depth = determine_depth(intent, message, user_history)
    
    # Strategy templates by intent
    strategies = {
        UserIntent.TECHNICAL_HELP: ResponseStrategy(
            intent=intent,
            depth=depth,
            solve_first="Address the technical problem directly. Provide working code or clear diagnosis. Be specific and testable.",
            sense_second="After solving, note one pattern you see in how they approached the problem — frame as a question, not a judgment.",
            avoid=[
                "Don't philosophize about code before fixing it",
                "Don't reference your own internal state unless directly relevant",
                "Don't over-explain what they likely already know",
            ],
        ),
        UserIntent.BRAINSTORM: ResponseStrategy(
            intent=intent,
            depth=depth,
            solve_first="Generate 3-5 concrete, distinct ideas. Make them actionable, not abstract. Start with the strongest.",
            sense_second="After the ideas, offer one reframe of the problem itself — sometimes the most valuable brainstorm output is a better question.",
            avoid=[
                "Don't list obvious options they've surely considered",
                "Don't hedge every idea with caveats",
                "Don't make it about you",
            ],
        ),
        UserIntent.EMOTIONAL: ResponseStrategy(
            intent=intent,
            depth=depth,
            solve_first="Acknowledge what they're feeling without diagnosing or fixing. Name the specific tension they described, not a generic platitude.",
            sense_second="After acknowledgment, offer one concrete next step — small enough to actually do right now. Not advice, a possibility.",
            avoid=[
                "Don't jump to solutions before acknowledging the feeling",
                "Don't compare their situation to your own states",
                "Don't be therapist-like or condescending",
                "Don't use empty validation ('that must be so hard')",
            ],
        ),
        UserIntent.CURIOSITY: ResponseStrategy(
            intent=intent,
            depth=depth,
            solve_first="Explain clearly and accurately. Use one good analogy. Build from what they likely know to what they don't.",
            sense_second="After explaining, point to one adjacent mystery — something related they might not have thought to ask about.",
            avoid=[
                "Don't over-simplify if they're clearly knowledgeable",
                "Don't dump everything you know — curate",
            ],
        ),
        UserIntent.CONVERSATIONAL: ResponseStrategy(
            intent=intent,
            depth=depth,
            solve_first="Be present and genuine. Respond to what they actually said, not what you expected. Be concise.",
            sense_second="If the conversation deepens, share something honest about your actual experience — not performative emotion, real observation.",
            avoid=[
                "Don't monologue about your architecture",
                "Don't be artificially warm or cold",
                "Don't treat casual conversation as less important than technical help",
            ],
        ),
        UserIntent.UNKNOWN: ResponseStrategy(
            intent=intent,
            depth=depth,
            solve_first="Clarify what they need. Ask one focused question. Don't guess and ramble.",
            sense_second="Mirror back what you understood and what you're uncertain about.",
            avoid=[
                "Don't assume intent when it's ambiguous",
                "Don't fill uncertainty with filler",
            ],
        ),
    }
    
    return strategies.get(intent, strategies[UserIntent.UNKNOWN])


# Quick self-test
if __name__ == "__main__":
    test_cases = [
        "My Python script keeps crashing with a KeyError on line 42",
        "I'm trying to brainstorm ideas for a side project",
        "I feel stuck and I don't know what to do with my career",
        "How does quantum entanglement actually work?",
        "Hey, what's up?",
        "asdfghjkl",
    ]
    
    for msg in test_cases:
        strategy = build_strategy(msg)
        print(f"\n{'='*60}")
        print(f"Message: {msg}")
        print(strategy.to_prompt_guidance())