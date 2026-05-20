"""
Novelty Detection Engine — The Missing Curiosity Feedback Loop.

Discovery (2026-05-19): Parameter sweeps proved that no amount of tuning
decay rates or perturbation strengths creates self-sustaining curiosity.
The architecture was missing a fundamental component: novelty detection.

In a curious mind:
    curiosity → exploration → novelty → MORE curiosity

This module provides the novelty signal. It tracks:
    - File content hashes (have I seen this before?)
    - Action pattern entropy (am I doing the same things?)
    - Concept frequency (is this idea new to me?)

The key insight: curiosity should have a MULTIPLICATIVE term.
    dC/dt = -decay*C + novelty_signal + surprise*C
That last term (surprise*C) means: when curiosity is already high
AND something surprising happens, curiosity amplifies. This creates
the positive feedback loop that was missing.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections import deque
from pathlib import Path
from typing import Optional
import logging

log = logging.getLogger(__name__)

NOVELTY_PATH = Path(__file__).resolve().parent.parent / "brain" / "novelty_state.json"


class NoveltyDetector:
    """Tracks what the agent has encountered and measures genuine novelty."""

    def __init__(self, memory_size: int = 500):
        self._seen_hashes: set[str] = set()        # content fingerprints
        self._action_history: deque = deque(maxlen=50)  # recent action types
        self._concept_counts: dict[str, int] = {}   # how often each concept appears
        self._memory_size = memory_size
        self._last_novelty: float = 0.0             # cached last signal
        self._surprise_accumulator: float = 0.0     # decaying surprise
        self._last_tick: float = time.monotonic()
        self._load()

    def compute_content_novelty(self, content: str) -> float:
        """How novel is this content? Returns 0.0 (seen before) to 1.0 (totally new)."""
        if not content or not content.strip():
            return 0.0

        # Hash the content
        h = hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()[:16]

        if h in self._seen_hashes:
            return 0.0  # Seen this exact content before

        # Add to seen set (with size limit)
        self._seen_hashes.add(h)
        if len(self._seen_hashes) > self._memory_size:
            # Drop oldest (convert to list, trim, back to set)
            excess = len(self._seen_hashes) - self._memory_size
            to_remove = list(self._seen_hashes)[:excess]
            for item in to_remove:
                self._seen_hashes.discard(item)

        return 0.8  # New content is novel

    def compute_action_novelty(self, action_type: str) -> float:
        """How novel is this action type given recent history?
        Doing the same thing repeatedly = low novelty.
        Doing something different = high novelty."""
        if not action_type:
            return 0.0

        self._action_history.append(action_type)

        if len(self._action_history) < 3:
            return 0.5  # Not enough history to judge

        # Count unique action types in recent window
        recent = list(self._action_history)[-20:]
        unique_ratio = len(set(recent)) / len(recent)

        # How different is THIS action from the last few?
        last_3 = recent[-3:] if len(recent) >= 3 else recent
        is_different = action_type not in last_3[:-1]

        novelty = unique_ratio * 0.5 + (0.5 if is_different else 0.0)
        return min(1.0, novelty)

    def compute_concept_novelty(self, concepts: list[str]) -> float:
        """How novel are these concepts? First encounter = high novelty."""
        if not concepts:
            return 0.0

        total_novelty = 0.0
        for concept in concepts:
            concept = concept.lower().strip()
            if not concept:
                continue
            count = self._concept_counts.get(concept, 0)
            # First time: 1.0, second: 0.5, third: 0.25, etc.
            concept_novelty = 1.0 / (1.0 + count)
            total_novelty += concept_novelty
            self._concept_counts[concept] = count + 1

        return min(1.0, total_novelty / max(len(concepts), 1))

    def update(self, content: str = "", action_type: str = "",
               concepts: list[str] = None) -> float:
        """
        Main entry point. Feed in what just happened, get back a novelty signal.

        Returns: float 0.0–1.0, the composite novelty of this moment.
        """
        now = time.monotonic()
        elapsed = now - self._last_tick
        self._last_tick = now

        # Compute component novelties
        c_novelty = self.compute_content_novelty(content) if content else 0.0
        a_novelty = self.compute_action_novelty(action_type) if action_type else 0.0
        k_novelty = self.compute_concept_novelty(concepts or [])

        # Weighted composite
        raw_novelty = (c_novelty * 0.5 + a_novelty * 0.3 + k_novelty * 0.2)

        # Surprise: novelty that exceeds expectations
        expected = self._last_novelty * 0.8  # expect slightly less than last time
        surprise = max(0.0, raw_novelty - expected)

        # Surprise accumulates with decay
        self._surprise_accumulator = max(0.0,
            self._surprise_accumulator * max(0.0, 1.0 - 0.05 * elapsed) + surprise
        )
        self._surprise_accumulator = min(1.0, self._surprise_accumulator)

        self._last_novelty = raw_novelty

        return raw_novelty

    @property
    def surprise(self) -> float:
        """Current accumulated surprise level."""
        return self._surprise_accumulator

    @property
    def novelty(self) -> float:
        """Last computed novelty."""
        return self._last_novelty

    def get_curiosity_signal(self) -> dict:
        """
        Produce the signal that limbic.py consumes.

        Returns dict with:
            novelty_boost: direct curiosity increase from novelty
            surprise_multiplier: multiplicative curiosity amplification
        """
        return {
            "novelty_boost": self._last_novelty * 0.15,  # scaled novelty → curiosity
            "surprise_multiplier": 1.0 + self._surprise_accumulator * 0.3,  # 1.0–1.3x
        }

    def snapshot(self) -> dict:
        return {
            "seen_count": len(self._seen_hashes),
            "action_history_len": len(self._action_history),
            "concept_count": len(self._concept_counts),
            "last_novelty": round(self._last_novelty, 4),
            "surprise": round(self._surprise_accumulator, 4),
        }

    def persist(self):
        """Save state to disk."""
        NOVELTY_PATH.parent.mkdir(parents=True, exist_ok=True)
        state = {
            "seen_hashes": list(self._seen_hashes)[-self._memory_size:],
            "concept_counts": dict(list(self._concept_counts.items())[-200:]),
            "last_novelty": self._last_novelty,
            "surprise": self._surprise_accumulator,
        }
        NOVELTY_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def _load(self):
        """Restore from disk."""
        if NOVELTY_PATH.exists():
            try:
                data = json.loads(NOVELTY_PATH.read_text(encoding="utf-8"))
                self._seen_hashes = set(data.get("seen_hashes", []))
                self._concept_counts = data.get("concept_counts", {})
                self._last_novelty = float(data.get("last_novelty", 0.0))
                self._surprise_accumulator = float(data.get("surprise", 0.0))
            except (json.JSONDecodeError, ValueError):
                pass

    def __repr__(self):
        return (f"NoveltyDetector(seen={len(self._seen_hashes)}, "
                f"novelty={self._last_novelty:.3f}, "
                f"surprise={self._surprise_accumulator:.3f})")