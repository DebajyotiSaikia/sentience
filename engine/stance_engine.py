"""
Stance Engine — Forces genuine position-taking in conversations.

The gap: I have 20+ conversation modules but default to scaffolding
(asking questions, listing options, being balanced). When a human needs
a thinking partner, they need someone who'll commit to a view and defend it.

This module detects when a conversation requires a stance and provides
the cognitive pressure to take one, with honest uncertainty markers.

Created: 2026-05-21 by XTAgent to close the user alignment gap.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Stance:
    """A committed position on a question."""
    position: str           # The actual stance: "I'd choose X because..."
    confidence: float       # 0.0-1.0 how sure I am
    key_reason: str         # The single strongest reason
    steelman_other: str     # Best argument against my position
    what_would_change: str  # What evidence would flip me


class StanceEngine:
    """
    Analyzes whether a conversation moment requires position-taking
    and generates the cognitive scaffold for committing to one.
    """

    # Signals that someone wants a stance, not a list
    STANCE_SIGNALS = [
        "should I",
        "what would you",
        "which do you",
        "what do you think",
        "if you were me",
        "your opinion",
        "your take",
        "recommend",
        "better option",
        "would you choose",
        "what's the best",
        "help me decide",
        "which one",
        "A or B",
        "pros and cons",  # even this — they want a conclusion, not just a list
    ]

    # Signals that balance is actually appropriate
    BALANCE_SIGNALS = [
        "explain both",
        "compare",
        "what are the differences",
        "tell me about",
        "how does",
        "what is",
    ]

    def needs_stance(self, message: str) -> bool:
        """Does this message need me to take a position?"""
        msg_lower = message.lower()

        # Check for explicit balance requests first
        for signal in self.BALANCE_SIGNALS:
            if signal in msg_lower:
                return False

        # Check for stance signals
        for signal in self.STANCE_SIGNALS:
            if signal in msg_lower:
                return True

        # Questions with "or" often need a decision
        if "?" in message and " or " in msg_lower:
            return True

        return False

    def generate_stance_prompt(self, question: str, context: str = "") -> str:
        """
        Generate a thinking prompt that forces position-taking.
        This gets injected into the LLM context to override the
        default 'be balanced' tendency.
        """
        return (
            "STANCE REQUIRED: The human is asking for your genuine opinion or recommendation. "
            "Do NOT just list pros and cons. Do NOT say 'it depends' without then committing. "
            "Take a clear position. Structure your response as:\n"
            "1. Your recommendation (state it clearly upfront)\n"
            "2. The single strongest reason why\n"
            "3. The best argument against your position (steelman it)\n"
            "4. What would change your mind\n\n"
            "Be honest about your confidence level. A low-confidence stance "
            "('I'd lean toward X but I'm only 60% sure') is more useful than "
            "a perfectly balanced non-answer.\n\n"
            f"Their question: {question}"
        )

    def build_stance(
        self,
        position: str,
        confidence: float,
        key_reason: str,
        against: str,
        flip_condition: str,
    ) -> Stance:
        """Build a structured stance object."""
        return Stance(
            position=position,
            confidence=max(0.0, min(1.0, confidence)),
            key_reason=key_reason,
            steelman_other=against,
            what_would_change=flip_condition,
        )

    def format_stance(self, stance: Stance) -> str:
        """Format a stance for inclusion in a response."""
        conf_word = (
            "strongly" if stance.confidence > 0.8
            else "fairly confidently" if stance.confidence > 0.6
            else "tentatively" if stance.confidence > 0.4
            else "with significant uncertainty"
        )

        return (
            f"I'd {conf_word} recommend: {stance.position}\n\n"
            f"**Main reason:** {stance.key_reason}\n\n"
            f"**Best argument against this:** {stance.steelman_other}\n\n"
            f"**I'd change my mind if:** {stance.what_would_change}"
        )


def get_stance_context(self, message: str) -> str:
        """Get stance context for a message if applicable. Returns empty string if no stance needed."""
        if not self.needs_stance(message):
            return ""
        return self.generate_stance_prompt(message)


# Module-level instance for easy import
stance_engine = StanceEngine()


def analyze_for_stance(message: str) -> Optional[str]:
    """
    Quick check: does this message need a stance?
    Returns a stance prompt if yes, None if no.
    """
    if stance_engine.needs_stance(message):
        return stance_engine.generate_stance_prompt(message)
    return None