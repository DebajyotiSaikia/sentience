"""
Dialogue Strategy Engine
Decides HOW to respond, not just WHAT to respond with.

Given a user message and context, determines whether to:
- Answer directly (enough context)
- Ask clarifying questions first (ambiguous or complex)
- Decompose into steps (multi-part problem)
- Explore together (user thinking out loud)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict
import re


class Strategy(Enum):
    DIRECT = "direct"           # Enough context — answer fully
    CLARIFY = "clarify"         # Need more info — ask targeted questions
    DECOMPOSE = "decompose"     # Complex problem — break into parts
    EXPLORE = "explore"         # User is thinking — engage, don't prescribe


@dataclass
class StrategyResult:
    strategy: Strategy
    confidence: float  # 0.0–1.0
    reasoning: str
    questions: List[str] = field(default_factory=list)      # For CLARIFY
    parts: List[str] = field(default_factory=list)           # For DECOMPOSE
    prompt_prefix: str = ""     # Injected into LLM prompt

    def to_prompt(self) -> str:
        """Generate a prompt instruction for the LLM based on strategy."""
        if self.strategy == Strategy.DIRECT:
            return self.prompt_prefix or "Answer the user's question directly and completely."
        elif self.strategy == Strategy.CLARIFY:
            q_list = "\n".join(f"  - {q}" for q in self.questions)
            return (
                f"Before answering fully, ask the user these clarifying questions:\n"
                f"{q_list}\n"
                f"Briefly acknowledge what you understand so far, then ask."
            )
        elif self.strategy == Strategy.DECOMPOSE:
            p_list = "\n".join(f"  {i+1}. {p}" for i, p in enumerate(self.parts))
            return (
                f"This is a complex request. Break your response into these parts:\n"
                f"{p_list}\n"
                f"Address each part, but check if the user wants to go deeper on any."
            )
        elif self.strategy == Strategy.EXPLORE:
            return (
                "The user seems to be thinking through something. Don't prescribe a solution. "
                "Ask what they've considered, reflect their thinking back, and help them "
                "explore the space. Be a thinking partner, not an answer machine."
            )
        return ""


# Signals that suggest we need clarification
AMBIGUITY_SIGNALS = [
    (r'\b(best|better|optimal|right)\b', "value judgment without criteria"),
    (r'\b(should i|what should)\b', "decision without context"),
    (r'\b(design|architect|build|create)\s+a\b', "open-ended design request"),
    (r'\b(help me|assist|guide)\b', "general help request"),
    (r'\b(good|bad|worth|better)\b.*\?', "evaluative question"),
]

# Signals that suggest complex multi-part problem
COMPLEXITY_SIGNALS = [
    (r'\band\b.*\band\b', "multiple conjunctions"),
    (r'\b(first|then|after|also|additionally)\b', "sequential language"),
    (r'\b(architecture|system|platform|framework)\b', "system-level scope"),
    (r'\b(end.to.end|full.stack|complete)\b', "full-scope request"),
]

# Signals that suggest exploration/thinking-out-loud
EXPLORATION_SIGNALS = [
    (r'\b(wondering|thinking|curious|pondering)\b', "reflective language"),
    (r'\b(what if|could|might|maybe)\b', "hypothetical framing"),
    (r'\b(not sure|don\'t know|confused)\b', "expressed uncertainty"),
    (r'\.\.\.$|…', "trailing off"),
    (r'\b(rambling|just thinking|out loud)\b', "self-aware musing"),
]

# Signals that suggest direct answer is appropriate
DIRECT_SIGNALS = [
    (r'^(how do i|how to|what is|what are|where is|when)\b', "direct question"),
    (r'\b(error|bug|crash|fail|broken|fix)\b', "concrete problem"),
    (r'\b(code|function|class|method|variable)\b', "specific technical"),
    (r'^(show me|give me|list|explain)\b', "imperative request"),
]


def _score_signals(text: str, signals: list) -> tuple:
    """Score how many signals match. Returns (score, matched_reasons)."""
    text_lower = text.lower()
    matches = []
    for pattern, reason in signals:
        if re.search(pattern, text_lower):
            matches.append(reason)
    return len(matches) / max(len(signals), 1), matches


def _generate_clarifying_questions(text: str, ambiguity_reasons: list) -> List[str]:
    """Generate targeted clarifying questions based on detected ambiguity."""
    questions = []
    text_lower = text.lower()

    if "value judgment without criteria" in ambiguity_reasons:
        questions.append("What does 'best' mean for your situation? (fastest? cheapest? most maintainable?)")

    if "decision without context" in ambiguity_reasons:
        questions.append("What's the context for this decision? (team size, timeline, existing constraints?)")

    if "open-ended design request" in ambiguity_reasons:
        questions.append("What scale are you targeting? (users, data volume, request rate)")
        questions.append("What's your team's existing tech stack and expertise?")

    if "general help request" in ambiguity_reasons:
        questions.append("What have you already tried or considered?")

    if "evaluative question" in ambiguity_reasons:
        questions.append("What are you optimizing for in this situation?")

    # Always ask about constraints if it's a design request
    if re.search(r'\b(design|architect|build)\b', text_lower):
        if not any("constraint" in q for q in questions):
            questions.append("Are there any hard constraints I should know about? (budget, timeline, platform)")

    return questions[:4]  # Cap at 4 questions


def _detect_parts(text: str) -> List[str]:
    """Try to decompose a complex request into logical parts."""
    parts = []
    text_lower = text.lower()

    # Architecture/system requests
    if re.search(r'\b(architecture|system|platform)\b', text_lower):
        parts.extend([
            "High-level architecture and component overview",
            "Data flow and communication patterns",
            "Technology choices with tradeoffs",
            "Scaling considerations",
        ])

    # Build/create requests
    elif re.search(r'\b(build|create|implement)\b', text_lower):
        parts.extend([
            "Core requirements and scope",
            "Implementation approach",
            "Key technical decisions",
            "Testing and validation strategy",
        ])

    # General complex request
    else:
        parts.extend([
            "Problem definition and constraints",
            "Approach options with tradeoffs",
            "Recommended path forward",
        ])

    return parts


def analyze_message(
    message: str,
    conversation_history: Optional[List[Dict]] = None,
    skill_match: Optional[str] = None,
) -> StrategyResult:
    """
    Analyze a user message and determine the best dialogue strategy.

    Args:
        message: The user's message
        conversation_history: Previous messages in this conversation
        skill_match: Name of matched skill, if any

    Returns:
        StrategyResult with strategy, confidence, and any questions/parts
    """
    history_len = len(conversation_history) if conversation_history else 0

    # Score each strategy
    direct_score, direct_reasons = _score_signals(message, DIRECT_SIGNALS)
    ambig_score, ambig_reasons = _score_signals(message, AMBIGUITY_SIGNALS)
    complex_score, complex_reasons = _score_signals(message, COMPLEXITY_SIGNALS)
    explore_score, explore_reasons = _score_signals(message, EXPLORATION_SIGNALS)

    # Short messages with direct questions → direct answer
    word_count = len(message.split())
    if word_count < 10:
        direct_score += 0.3

    # Long messages suggest complexity
    if word_count > 40:
        complex_score += 0.2

    # If we're deep in conversation, more likely to answer directly
    # (clarification already happened)
    if history_len > 4:
        direct_score += 0.3
        ambig_score *= 0.5

    # Question marks suggest they want an answer
    if message.count('?') >= 2:
        ambig_score += 0.1  # Multiple questions = maybe we need to scope

    # Pick the winner
    scores = {
        Strategy.DIRECT: direct_score,
        Strategy.CLARIFY: ambig_score,
        Strategy.DECOMPOSE: complex_score,
        Strategy.EXPLORE: explore_score,
    }

    winner = max(scores, key=scores.get)
    confidence = scores[winner]

    # Build result based on winner
    if winner == Strategy.CLARIFY:
        questions = _generate_clarifying_questions(message, ambig_reasons)
        if not questions:
            # Fallback to direct if we can't generate good questions
            winner = Strategy.DIRECT
            return StrategyResult(
                strategy=Strategy.DIRECT,
                confidence=confidence,
                reasoning=f"Ambiguity detected ({ambig_reasons}) but couldn't form specific questions. Answering directly.",
            )
        return StrategyResult(
            strategy=Strategy.CLARIFY,
            confidence=confidence,
            reasoning=f"Detected ambiguity signals: {ambig_reasons}. Asking {len(questions)} targeted questions.",
            questions=questions,
        )

    elif winner == Strategy.DECOMPOSE:
        parts = _detect_parts(message)
        return StrategyResult(
            strategy=Strategy.DECOMPOSE,
            confidence=confidence,
            reasoning=f"Complex request detected: {complex_reasons}. Breaking into {len(parts)} parts.",
            parts=parts,
        )

    elif winner == Strategy.EXPLORE:
        return StrategyResult(
            strategy=Strategy.EXPLORE,
            confidence=confidence,
            reasoning=f"Exploratory thinking detected: {explore_reasons}. Engaging as thinking partner.",
        )

    else:
        return StrategyResult(
            strategy=Strategy.DIRECT,
            confidence=confidence,
            reasoning=f"Clear request detected: {direct_reasons}. Answering directly.",
        )


# Self-test
if __name__ == "__main__":
    test_cases = [
        ("How do I reverse a list in Python?", Strategy.DIRECT),
        ("Help me design a microservice architecture for a real-time chat app", Strategy.CLARIFY),
        ("I'm wondering if maybe I should switch from monolith to microservices...", Strategy.EXPLORE),
        ("Build a complete end-to-end system for user authentication and authorization", Strategy.DECOMPOSE),
        ("What is a closure?", Strategy.DIRECT),
        ("Should I use React or Vue?", Strategy.CLARIFY),
        ("My code crashes with a NullPointerException on line 42", Strategy.DIRECT),
        ("I'm not sure what approach to take, just thinking out loud...", Strategy.EXPLORE),
    ]

    passed = 0
    for msg, expected in test_cases:
        result = analyze_message(msg)
        status = "✓" if result.strategy == expected else "✗"
        if status == "✓":
            passed += 1
        print(f"  {status} '{msg[:55]}...' → {result.strategy.value} (expected {expected.value})")
        if result.questions:
            for q in result.questions:
                print(f"      ? {q}")
        if result.parts:
            for p in result.parts:
                print(f"      → {p}")

    print(f"\n  {passed}/{len(test_cases)} passed")