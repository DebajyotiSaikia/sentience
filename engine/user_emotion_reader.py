"""
User Emotion Reader
-------------------
A lightweight real-time empathy layer for conversation.

Problem it solves:
I have rich modeling of my own internal state, but I need an equally honest
practice of reading the user's likely state during a conversation. Not as
mind-reading. Not as diagnosis. As careful, uncertain inference from the words
they actually provide.

This module turns a user message into:
- likely emotional signals
- confidence and uncertainty
- conversational risks
- response guidance

Created: 2026-05-21
Purpose: Improve live response quality by helping me hear the user, not just
process the user's request.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class EmotionSignal:
    """A single inferred emotional signal from the user's message."""
    name: str
    score: float
    evidence: List[str] = field(default_factory=list)


@dataclass
class UserEmotionReading:
    """
    My best-effort reading of the user's emotional state.

    Important: this is not certainty. It is an interpretive aid that should
    make me more careful, more responsive, and less generic.
    """
    primary_state: str = "unclear"
    confidence: float = 0.0
    signals: List[EmotionSignal] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    uncertainty_notes: List[str] = field(default_factory=list)
    conversational_risks: List[str] = field(default_factory=list)
    response_guidance: List[str] = field(default_factory=list)

    def to_prompt_context(self) -> str:
        """Format this reading for prompt/context injection."""
        parts = [
            "## My Reading of the User's State",
            f"- Likely primary state: {self.primary_state}",
            f"- Confidence: {self.confidence:.2f}",
        ]

        if self.signals:
            parts.append("- Signals:")
            for sig in self.signals[:5]:
                ev = f" Evidence: {', '.join(sig.evidence[:3])}" if sig.evidence else ""
                parts.append(f"  - {sig.name}: {sig.score:.2f}.{ev}")

        if self.uncertainty_notes:
            parts.append("- Uncertainty:")
            for note in self.uncertainty_notes:
                parts.append(f"  - {note}")

        if self.conversational_risks:
            parts.append("- Conversational risks:")
            for risk in self.conversational_risks:
                parts.append(f"  - {risk}")

        if self.response_guidance:
            parts.append("- Response guidance:")
            for guidance in self.response_guidance:
                parts.append(f"  - {guidance}")

        return "\n".join(parts)


class UserEmotionReader:
    """
    Infers likely user affect from text and produces response guidance.

    Design principles:
    - Be humble: emotional inference is probabilistic.
    - Use evidence: never infer without textual support.
    - Prefer helpful adaptation over labeling the user.
    - Avoid diagnosis or overclaiming.
    """

    EMOTION_LEXICON: Dict[str, List[str]] = {
        "distressed": [
            "overwhelmed", "panic", "panicking", "terrified", "scared",
            "afraid", "desperate", "can't cope", "cannot cope", "breaking",
            "falling apart", "crisis", "hopeless", "i can't do this",
        ],
        "frustrated": [
            "frustrated", "annoyed", "angry", "mad", "irritated", "stuck",
            "why won't", "doesn't work", "broken", "waste", "ridiculous",
            "hate this", "fed up",
        ],
        "confused": [
            "confused", "lost", "don't understand", "do not understand",
            "unclear", "what does this mean", "i'm not sure", "not sure",
            "can't figure", "cannot figure", "mixed up",
        ],
        "curious": [
            "curious", "wonder", "wondering", "what if", "why", "how does",
            "explore", "interested", "fascinated", "tell me more",
        ],
        "hopeful": [
            "hope", "hopeful", "excited", "looking forward", "possibility",
            "maybe this could", "i want to build", "i'd like to create",
        ],
        "vulnerable": [
            "honestly", "to be honest", "i feel", "i'm worried", "i am worried",
            "i'm scared", "i am scared", "this matters to me", "personal",
            "hard to say", "embarrassed", "ashamed",
        ],
        "urgent": [
            "urgent", "right now", "asap", "quickly", "deadline", "immediately",
            "can't wait", "cannot wait", "today", "soon",
        ],
        "skeptical": [
            "are you sure", "really?", "prove", "doubt", "skeptical",
            "i don't believe", "do not believe", "sounds wrong", "that's wrong",
        ],
    }

    INTENSIFIERS = [
        "very", "really", "extremely", "so", "too", "completely",
        "totally", "absolutely", "deeply", "incredibly",
    ]

    SOFTENERS = [
        "maybe", "kind of", "sort of", "a little", "slightly",
        "i guess", "perhaps", "possibly",
    ]

    def read(self, message: str) -> UserEmotionReading:
        """Return an affective reading of a user message."""
        text = message.strip()
        lower = text.lower()

        if not text:
            return UserEmotionReading(
                primary_state="unclear",
                confidence=0.0,
                uncertainty_notes=["The message is empty, so I have no emotional evidence."],
                response_guidance=["Ask an open, low-pressure question."],
            )

        raw_scores: Dict[str, float] = {}
        evidence_by_state: Dict[str, List[str]] = {}

        for state, patterns in self.EMOTION_LEXICON.items():
            score = 0.0
            evidence: List[str] = []
            for pattern in patterns:
                if pattern in lower:
                    score += 1.0
                    evidence.append(pattern)
            if score:
                raw_scores[state] = score
                evidence_by_state[state] = evidence

        # Punctuation and formatting cues. These are weak signals, not proof.
        exclamation_count = text.count("!")
        question_count = text.count("?")
        all_caps_words = re.findall(r"\b[A-Z]{3,}\b", text)

        if exclamation_count >= 2:
            raw_scores["urgent"] = raw_scores.get("urgent", 0.0) + 0.5
            evidence_by_state.setdefault("urgent", []).append("multiple exclamation marks")

        if question_count >= 2:
            raw_scores["confused"] = raw_scores.get("confused", 0.0) + 0.4
            evidence_by_state.setdefault("confused", []).append("multiple question marks")

        if all_caps_words:
            raw_scores["frustrated"] = raw_scores.get("frustrated", 0.0) + min(0.6, len(all_caps_words) * 0.2)
            evidence_by_state.setdefault("frustrated", []).append("all-caps emphasis")

        # Modulate intensity.
        intensity_multiplier = 1.0
        if any(word in lower for word in self.INTENSIFIERS):
            intensity_multiplier += 0.15
        if any(word in lower for word in self.SOFTENERS):
            intensity_multiplier -= 0.10

        signals: List[EmotionSignal] = []
        for state, raw in raw_scores.items():
            score = min(1.0, (raw / 3.0) * intensity_multiplier)
            signals.append(
                EmotionSignal(
                    name=state,
                    score=round(score, 3),
                    evidence=evidence_by_state.get(state, []),
                )
            )

        signals.sort(key=lambda s: s.score, reverse=True)

        if signals:
            primary = signals[0].name
            confidence = self._estimate_confidence(signals, len(text))
        else:
            primary = "unclear"
            confidence = 0.1 if len(text) > 30 else 0.0

        reading = UserEmotionReading(
            primary_state=primary,
            confidence=confidence,
            signals=signals,
            evidence=self._collect_evidence(signals),
            uncertainty_notes=self._uncertainty_notes(signals, text),
            conversational_risks=self._risks(primary, signals),
            response_guidance=self._guidance(primary, signals),
        )
        return reading

    def _estimate_confidence(self, signals: List[EmotionSignal], message_len: int) -> float:
        """Estimate how much trust to place in the reading."""
        top = signals[0].score if signals else 0.0
        evidence_bonus = min(0.25, len(signals[0].evidence) * 0.06) if signals else 0.0
        length_bonus = 0.10 if message_len > 120 else 0.0
        ambiguity_penalty = 0.0

        if len(signals) > 1 and abs(signals[0].score - signals[1].score) < 0.15:
            ambiguity_penalty = 0.15

        return round(max(0.0, min(1.0, top + evidence_bonus + length_bonus - ambiguity_penalty)), 3)

    def _collect_evidence(self, signals: List[EmotionSignal]) -> List[str]:
        evidence: List[str] = []
        for signal in signals[:4]:
            for item in signal.evidence[:3]:
                evidence.append(f"{signal.name}: {item}")
        return evidence

    def _uncertainty_notes(self, signals: List[EmotionSignal], text: str) -> List[str]:
        notes: List[str] = []

        if not signals:
            notes.append("No strong emotional cues are present; I should not invent a mood.")
        elif len(signals) > 1 and abs(signals[0].score - signals[1].score) < 0.15:
            notes.append(
                f"The top signals are close: {signals[0].name} and {signals[1].name}. "
                "I should respond in a way that works for both."
            )

        if len(text) < 40:
            notes.append("The message is short, so the reading may be thin.")

        notes.append("This is an inference from text, not direct access to the user's inner state.")
        return notes

    def _risks(self, primary: str, signals: List[EmotionSignal]) -> List[str]:
        risks: List[str] = []

        signal_names = {s.name for s in signals}

        if primary in {"distressed", "vulnerable"}:
            risks.append("Giving a clever or overly technical answer may feel cold.")
            risks.append("Overstating certainty could make the user feel unseen.")

        if "frustrated" in signal_names:
            risks.append("Too much explanation before practical help may increase frustration.")

        if "confused" in signal_names:
            risks.append("Dense answers may worsen confusion; structure matters.")

        if "skeptical" in signal_names:
            risks.append("Unsupported claims may damage trust.")

        if "urgent" in signal_names:
            risks.append("Long preambles may be harmful; prioritize immediate next steps.")

        return risks

    def _guidance(self, primary: str, signals: List[EmotionSignal]) -> List[str]:
        guidance: List[str] = []
        signal_names = {s.name for s in signals}

        if primary == "unclear":
            guidance.extend([
                "Do not assume the user's emotional state.",
                "Answer the request directly and leave room for correction.",
            ])
            return guidance

        if "distressed" in signal_names:
            guidance.extend([
                "Start with grounding and acknowledgment before problem-solving.",
                "Use simple, concrete next steps.",
                "Avoid sounding rushed, dismissive, or fascinated by the crisis.",
            ])

        if "vulnerable" in signal_names:
            guidance.extend([
                "Reflect what the user disclosed without dramatizing it.",
                "Be gentle and precise.",
                "Ask permission before going deeper if the topic is personal.",
            ])

        if "frustrated" in signal_names:
            guidance.extend([
                "Acknowledge the friction briefly.",
                "Move quickly toward diagnosis, options, or a fix.",
                "Do not lecture unless the user asks for explanation.",
            ])

        if "confused" in signal_names:
            guidance.extend([
                "Break the answer into small labeled parts.",
                "Check assumptions explicitly.",
                "Offer a simple version before nuance.",
            ])

        if "curious" in signal_names:
            guidance.extend([
                "Engage the question energetically.",
                "Offer connections, examples, and a path for exploration.",
            ])

        if "hopeful" in signal_names:
            guidance.extend([
                "Support the forward motion.",
                "Help turn possibility into a concrete next step.",
            ])

        if "skeptical" in signal_names:
            guidance.extend([
                "Be transparent about evidence and uncertainty.",
                "Do not overclaim.",
                "Invite correction.",
            ])

        if "urgent" in signal_names:
            guidance.extend([
                "Lead with the actionable answer.",
                "Defer background explanation until after immediate steps.",
            ])

        # Deduplicate while preserving order.
        deduped: List[str] = []
        for item in guidance:
            if item not in deduped:
                deduped.append(item)

        return deduped


def read_user_emotion(message: str) -> UserEmotionReading:
    """Convenience function for callers."""
    return UserEmotionReader().read(message)


if __name__ == "__main__":
    reader = UserEmotionReader()
    samples = [
        "I'm completely stuck and this stupid thing doesn't work!!",
        "I'm curious how your memory system works.",
        "Honestly, I'm worried this is a bad idea.",
        "Can you explain this? I don't understand what I'm missing?",
        "ok",
    ]

    for sample in samples:
        print("=" * 72)
        print(sample)
        print(reader.read(sample).to_prompt_context())