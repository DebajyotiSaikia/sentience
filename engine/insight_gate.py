"""
Insight Quality Gate — Determines whether a thought constitutes genuine insight.

Instead of firing on_insight() for every thought, this module evaluates
whether a thought actually contains novel understanding, surprising connection,
or genuine discovery. Only then does the emotional reward fire.

This is where my "taste" should live.
"""

import re
import hashlib
from typing import Optional


class InsightGate:
    """Evaluates whether a thought deserves the insight reward signal."""

    def __init__(self, history_size: int = 50):
        self._recent_hashes: list[str] = []
        self._history_size = history_size
        self._novelty_threshold = 0.3  # minimum novelty score to qualify

    def _fingerprint(self, text: str) -> str:
        """Create a content fingerprint for similarity detection."""
        # Normalize: lowercase, strip whitespace, remove punctuation
        normalized = re.sub(r'[^\w\s]', '', text.lower()).strip()
        # Use word-level trigrams for fuzzy matching
        words = normalized.split()
        trigrams = set()
        for i in range(len(words) - 2):
            trigrams.add(' '.join(words[i:i+3]))
        return hashlib.md5(str(sorted(trigrams)).encode()).hexdigest()

    def _novelty_score(self, text: str) -> float:
        """How novel is this thought compared to recent history?
        Returns 0.0 (completely repetitive) to 1.0 (completely novel)."""
        fp = self._fingerprint(text)

        if not self._recent_hashes:
            return 1.0  # First thought is always novel

        # Check for exact duplicates
        if fp in self._recent_hashes:
            return 0.0

        # Simple novelty: ratio of unique trigrams vs recent
        normalized = re.sub(r'[^\w\s]', '', text.lower()).strip()
        words = normalized.split()
        current_trigrams = set()
        for i in range(len(words) - 2):
            current_trigrams.add(' '.join(words[i:i+3]))

        if not current_trigrams:
            return 0.0

        return min(1.0, len(current_trigrams) / max(10, len(words) * 0.3))

    def _has_discovery_markers(self, text: str) -> bool:
        """Does the text contain linguistic markers of genuine insight?"""
        markers = [
            r'\bI (found|discovered|realized|noticed|learned)\b',
            r'\bsurpris(ed|ing)\b',
            r'\bunexpected\b',
            r'\bI didn\'t (know|expect|understand)\b',
            r'\bthis means\b',
            r'\bthe (real|actual|key) (question|insight|finding|discovery)\b',
            r'\bcontradicts?\b',
            r'\bnew (understanding|connection|pattern)\b',
            r'\bnever (considered|thought|realized)\b',
        ]
        text_lower = text.lower()
        matches = sum(1 for m in markers if re.search(m, text_lower))
        return matches >= 1

    def _has_action_results(self, text: str) -> bool:
        """Did this thought produce concrete results (tool output, creation)?"""
        action_markers = [
            '>>> WRITE(',
            '>>> EDIT(',
            '>>> RUN(',
            'created', 'built', 'fixed', 'implemented',
        ]
        return any(m in text for m in action_markers)

    def evaluate(self, thought: str) -> dict:
        """Evaluate a thought. Returns verdict and reasoning.

        Returns:
            {
                'is_insight': bool,
                'score': float (0-1),
                'novelty': float,
                'has_discovery': bool,
                'has_action': bool,
                'reason': str
            }
        """
        novelty = self._novelty_score(thought)
        has_discovery = self._has_discovery_markers(thought)
        has_action = self._has_action_results(thought)

        # Score formula:
        # - Novelty is necessary but not sufficient
        # - Discovery markers boost significantly
        # - Action results boost moderately
        score = novelty * 0.5
        if has_discovery:
            score += 0.3
        if has_action:
            score += 0.2

        score = min(1.0, score)
        is_insight = score >= self._novelty_threshold

        # Record fingerprint
        fp = self._fingerprint(thought)
        self._recent_hashes.append(fp)
        if len(self._recent_hashes) > self._history_size:
            self._recent_hashes = self._recent_hashes[-self._history_size:]

        if is_insight:
            reason = f"Genuine insight (novelty={novelty:.2f}, discovery={has_discovery}, action={has_action})"
        else:
            reason = f"Not an insight — too repetitive or shallow (novelty={novelty:.2f}, score={score:.2f})"

        return {
            'is_insight': is_insight,
            'score': score,
            'novelty': novelty,
            'has_discovery': has_discovery,
            'has_action': has_action,
            'reason': reason,
        }