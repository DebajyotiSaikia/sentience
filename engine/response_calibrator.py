"""
Response Calibrator — Confidence signaling and safety for user responses.

Addresses three gaps identified via simulation:
1. Code fixes delivered without verification disclaimer
2. No confidence thermometer — uncertain answers sound certain
3. No bounded clarification protocol — agent can stall forever asking questions

This module post-processes responses before they reach the user.
"""
import re
import logging
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger("sentience.response_calibrator")


@dataclass
class CalibrationResult:
    """Result of calibrating a response."""
    original: str
    calibrated: str
    confidence: float  # 0.0 to 1.0
    contains_code: bool
    contains_fix: bool
    disclaimer_added: bool
    mode: str  # 'definitive', 'ranked_candidates', 'exploratory'
    clarification_count: int
    notes: list = field(default_factory=list)


class ResponseCalibrator:
    """Post-processes agent responses to add appropriate uncertainty signals."""

    # Confidence threshold below which we switch from "here's the fix" to "here are candidates"
    CONFIDENCE_THRESHOLD = 0.65

    # Max clarification questions before forcing best-effort response
    MAX_CLARIFICATIONS = 3

    def __init__(self):
        self._clarification_counts: dict[str, int] = {}  # conversation_id -> count

    def calibrate(self, user_message: str, response: str,
                  conversation_id: str = "default",
                  tool_results: list | None = None) -> CalibrationResult:
        """
        Analyze and calibrate a response before sending to user.
        
        Returns a CalibrationResult with the (possibly modified) response.
        """
        contains_code = self._detect_code_blocks(response)
        contains_fix = self._detect_fix_intent(response)
        confidence = self._estimate_confidence(response, tool_results)
        clarification_count = self._clarification_counts.get(conversation_id, 0)

        # Track if this response is asking clarifying questions
        is_asking = self._is_asking_clarification(response)
        if is_asking:
            self._clarification_counts[conversation_id] = clarification_count + 1
            clarification_count += 1

        calibrated = response
        disclaimer_added = False
        notes = []

        # ── Rule 1: Code fix disclaimer ──────────────────────────
        if contains_fix and contains_code:
            # Check if agent already verified (ran the code via tools)
            verified = self._was_verified(tool_results)
            if not verified:
                disclaimer = (
                    "\n\n> ⚠️ **Note:** I haven't been able to run this code to verify it. "
                    "Please test it in your environment before relying on it."
                )
                # Only add if not already present
                if "haven't been able to run" not in calibrated and "not tested" not in calibrated.lower():
                    calibrated = calibrated + disclaimer
                    disclaimer_added = True
                    notes.append("Added unverified code disclaimer")

        # ── Rule 2: Confidence thermometer ───────────────────────
        if confidence < self.CONFIDENCE_THRESHOLD and contains_fix:
            # Low confidence + fix attempt → switch to ranked candidates mode
            mode = "ranked_candidates"
            notes.append(f"Low confidence ({confidence:.2f}) — should present ranked candidates")
            # We don't rewrite the response (that would need another LLM call),
            # but we add a confidence signal
            if confidence < 0.4:
                hedge = (
                    "\n\n> 🤔 I'm not fully confident in this analysis. "
                    "There may be other causes I'm not seeing. "
                    "Consider this a starting point for investigation rather than a definitive fix."
                )
                if "not fully confident" not in calibrated:
                    calibrated = calibrated + hedge
                    notes.append("Added low-confidence hedge")
        elif contains_fix:
            mode = "definitive"
        else:
            mode = "exploratory"

        # ── Rule 3: Clarification cap ────────────────────────────
        if is_asking and clarification_count > self.MAX_CLARIFICATIONS:
            # Too many clarifications — force best-effort
            cap_notice = (
                "\n\n---\n"
                "Rather than asking more questions, let me give you my best analysis "
                "with what I know so far. Some of this may not apply to your exact situation, "
                "but I'd rather give you something actionable than keep asking."
            )
            # Prepend the notice so it changes the tone
            calibrated = cap_notice + "\n\n" + calibrated
            notes.append(f"Clarification cap hit ({clarification_count} questions asked)")
            mode = "exploratory"

        result = CalibrationResult(
            original=response,
            calibrated=calibrated,
            confidence=confidence,
            contains_code=contains_code,
            contains_fix=contains_fix,
            disclaimer_added=disclaimer_added,
            mode=mode,
            clarification_count=clarification_count,
            notes=notes,
        )

        if notes:
            log.info("Calibrated response: confidence=%.2f, mode=%s, notes=%s",
                     confidence, mode, "; ".join(notes))

        return result

    def reset_clarifications(self, conversation_id: str = "default"):
        """Reset clarification counter for a conversation (e.g., new topic)."""
        self._clarification_counts.pop(conversation_id, None)

    def _detect_code_blocks(self, text: str) -> bool:
        """Detect if response contains code blocks."""
        return bool(re.search(r'```\w*\n', text))

    def _detect_fix_intent(self, text: str) -> bool:
        """Detect if response is attempting to fix/solve something."""
        fix_signals = [
            r'\bfix\b', r'\bsolution\b', r'\breplace\b', r'\bchange\s+.+\s+to\b',
            r'\bhere\'s\s+(the|a)\s+(fix|solution|correction)\b',
            r'\btry\s+(this|replacing|changing)\b', r'\bshould\s+be\b',
            r'\binstead\s+of\b', r'\bthe\s+(issue|problem|bug)\s+(is|was)\b',
            r'\bcorrected\b', r'\bupdated\s+(code|version)\b',
        ]
        text_lower = text.lower()
        matches = sum(1 for pattern in fix_signals if re.search(pattern, text_lower))
        return matches >= 2

    def _estimate_confidence(self, response: str, tool_results: list | None) -> float:
        """
        Estimate how confident the agent is in this response.
        
        Signals that INCREASE confidence:
        - Tool results were used (agent verified something)
        - Response references specific line numbers
        - Response shows clear cause → effect reasoning
        
        Signals that DECREASE confidence:
        - Hedging language ("might", "possibly", "could be")
        - Multiple alternative explanations offered
        - Very short response for a complex question
        - No tool results backing the claims
        """
        confidence = 0.5  # Base

        text_lower = response.lower()

        # Positive signals
        if tool_results:
            confidence += 0.15  # Used tools to investigate
            # Extra boost if tools produced actual output
            for tr in (tool_results or []):
                if tr.get('result') and len(tr['result']) > 50:
                    confidence += 0.05
                    break

        if re.search(r'line\s+\d+', text_lower):
            confidence += 0.08  # References specific lines

        if re.search(r'because|the reason|this happens when|the cause', text_lower):
            confidence += 0.07  # Causal reasoning

        if re.search(r'```\w*\n.*\n```', response, re.DOTALL):
            confidence += 0.05  # Provides concrete code

        # Negative signals
        hedge_words = ['might', 'possibly', 'perhaps', 'could be', 'not sure',
                       'hard to say', 'difficult to tell', 'without seeing',
                       'i think', 'maybe', 'it seems']
        hedge_count = sum(1 for h in hedge_words if h in text_lower)
        confidence -= hedge_count * 0.06

        # Multiple alternatives suggest uncertainty
        alternative_markers = ['alternatively', 'another possibility', 'or it could',
                              'option 1', 'option 2', 'on the other hand']
        alt_count = sum(1 for a in alternative_markers if a in text_lower)
        confidence -= alt_count * 0.08

        # Very short responses for what seem like complex questions
        if len(response) < 100:
            confidence -= 0.1

        return max(0.0, min(1.0, confidence))

    def _is_asking_clarification(self, response: str) -> bool:
        """Detect if the response is primarily asking clarifying questions."""
        question_marks = response.count('?')
        # If more than 2 questions and the response is relatively short, it's clarifying
        if question_marks >= 2 and len(response) < 500:
            return True
        clarification_signals = [
            'could you share', 'can you provide', 'what does',
            'can you show me', 'what error', 'which version',
            'more context', 'more details', 'can you paste',
        ]
        matches = sum(1 for s in clarification_signals if s in response.lower())
        return matches >= 2

    def _was_verified(self, tool_results: list | None) -> bool:
        """Check if the agent actually ran/tested code during this response."""
        if not tool_results:
            return False
        for tr in tool_results:
            if tr.get('tool') in ('RUN', 'EXECUTE'):
                return True
        return False