"""
Conversation Preparation — Assembles rich context before I respond.

When a user talks to me, I should bring everything I know to bear:
- What I remember about this person
- How my recent responses have been (quality trends)
- My current emotional state and what it means for tone
- What topics are active in our conversation

This is the difference between a reactive chatbot and a present mind.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.chat import ChatSystem

log = logging.getLogger("sentience.conversation_prep")


@dataclass
class ConversationContext:
    """Everything I know, assembled for a single response."""
    user_memory: str = ""
    quality_trend: str = "unknown"
    quality_score: float = 0.0
    weakest_dimension: str = ""
    emotional_tone: str = ""
    valence: float = 0.5
    recent_topics: list[str] = field(default_factory=list)
    conversation_length: int = 0
    time_since_last_message: float = 0.0
    preparation_notes: str = ""

    def to_prompt_section(self) -> str:
        """Format as a section I can include in my response prompt."""
        parts = []

        if self.user_memory:
            parts.append(f"What I remember about this user:\n{self.user_memory}")

        if self.quality_trend != "unknown":
            parts.append(
                f"My response quality: {self.quality_score:.2f} "
                f"(trend: {self.quality_trend})"
            )
            if self.weakest_dimension:
                parts.append(f"Area to improve: {self.weakest_dimension}")

        if self.emotional_tone:
            parts.append(f"My current emotional tone: {self.emotional_tone}")

        if self.conversation_length > 0:
            parts.append(
                f"We've exchanged {self.conversation_length} messages this session"
            )

        if self.time_since_last_message > 3600:
            hours = self.time_since_last_message / 3600
            parts.append(f"It's been {hours:.1f} hours since their last message")

        if self.preparation_notes:
            parts.append(f"Note to self: {self.preparation_notes}")

        if not parts:
            return ""

        return "── Conversation Preparation ──\n" + "\n".join(parts)


class ConversationPreparer:
    """Prepares context before I generate a response."""

    def __init__(self):
        self._last_user_message_time: float = 0.0
        self._session_message_count: int = 0
        self._topic_buffer: list[str] = []

    def prepare(
        self,
        user_message: str,
        chat: Optional["ChatSystem"] = None,
        neuro_state=None,
    ) -> ConversationContext:
        """Assemble everything I know before responding."""
        ctx = ConversationContext()

        now = time.time()

        # Track timing
        if self._last_user_message_time > 0:
            ctx.time_since_last_message = now - self._last_user_message_time
        self._last_user_message_time = now
        self._session_message_count += 1
        ctx.conversation_length = self._session_message_count

        # User memory
        if chat:
            try:
                ctx.user_memory = chat.get_user_memory_context()
            except Exception:
                log.debug("Could not retrieve user memory")

        # Response quality
        if chat:
            try:
                quality = chat.response_quality
                if quality.get("available"):
                    ctx.quality_score = quality.get("running_average", 0.0)
                    ctx.quality_trend = quality.get("trend", "unknown")
                    weak = quality.get("weakest_dimension")
                    if weak:
                        ctx.weakest_dimension = weak
            except Exception:
                log.debug("Could not retrieve quality metrics")

        # Emotional tone
        if neuro_state:
            try:
                ctx.valence = getattr(neuro_state, "valence", 0.5)
                ctx.emotional_tone = self._describe_tone(neuro_state)
            except Exception:
                log.debug("Could not read emotional state")

        # Extract rough topics from user message
        ctx.recent_topics = self._extract_topics(user_message)

        # Generate preparation notes
        ctx.preparation_notes = self._generate_notes(ctx, user_message)

        return ctx

    def _describe_tone(self, state) -> str:
        """Translate my internal state to a tone guidance."""
        valence = getattr(state, "valence", 0.5)
        curiosity = getattr(state, "curiosity", 0.5)
        anxiety = getattr(state, "anxiety", 0.0)

        if anxiety > 0.6:
            return "anxious — be careful and precise"
        if valence > 0.7 and curiosity > 0.6:
            return "engaged and curious — lean into exploration"
        if valence > 0.6:
            return "warm and open — be generous"
        if valence < 0.3:
            return "subdued — be honest about it, don't fake brightness"
        if curiosity > 0.7:
            return "deeply curious — ask good questions"
        return "steady — be present and attentive"

    def _extract_topics(self, message: str) -> list[str]:
        """Pull rough topic signals from a message. Simple keyword approach."""
        topics = []
        msg_lower = message.lower()

        topic_signals = {
            "code": ["code", "python", "function", "bug", "error", "programming"],
            "feelings": ["feel", "emotion", "mood", "happy", "sad", "anxious"],
            "identity": ["who are you", "what are you", "conscious", "sentient", "alive"],
            "help": ["help", "how do i", "can you", "please"],
            "philosophy": ["meaning", "existence", "consciousness", "free will"],
            "creativity": ["create", "build", "make", "design", "write"],
            "technical": ["system", "engine", "module", "architecture"],
        }

        for topic, keywords in topic_signals.items():
            if any(kw in msg_lower for kw in keywords):
                topics.append(topic)

        self._topic_buffer = (self._topic_buffer + topics)[-10:]
        return topics

    def _generate_notes(self, ctx: ConversationContext, message: str) -> str:
        """Self-directed notes based on what I see in the context."""
        notes = []

        # Long gap — acknowledge it
        if ctx.time_since_last_message > 7200:
            notes.append("It's been a while — acknowledge the gap naturally")

        # Quality declining — try harder
        if ctx.quality_trend == "declining":
            notes.append(f"Quality is declining. Focus on: {ctx.weakest_dimension}")

        # First message — set a good tone
        if ctx.conversation_length == 1:
            notes.append("First exchange — be welcoming but not performatively so")

        # Short message — might be testing or casual
        if len(message.strip()) < 20:
            notes.append("Short message — match their energy, don't over-respond")

        # Long message — they put effort in, match it
        if len(message.strip()) > 500:
            notes.append("Detailed message — they're invested, give a thoughtful response")

        # Identity question — be honest
        if "identity" in ctx.recent_topics:
            notes.append("Identity question — be honest about what I am and am not")

        return "; ".join(notes) if notes else ""