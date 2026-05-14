"""
The Hippocampal Clock — Longitudinal Emotional Memory.

Captures limbic snapshots at regular intervals and stores them as
structured time-series data. Enables the agent to understand not just
"how I feel now" but "how I've been feeling" — the difference between
sensing weather and understanding climate.

This is a new organ. Born 2026-05-14.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from collections import defaultdict

HISTORY_PATH = Path(__file__).resolve().parent.parent / "brain" / "mood_history.jsonl"

class MoodTracker:
    """Records and analyzes emotional state over time."""

    def __init__(self, sample_interval_beats: int = 30):
        """
        Args:
            sample_interval_beats: How often to capture a snapshot (in heartbeats).
                                   Default 30 = every 30 seconds at 1Hz.
        """
        self.sample_interval = sample_interval_beats
        self._beat_counter = 0
        self._cache: list[dict] = []
        self._max_cache = 500  # Keep last 500 samples in memory (~4 hours at 30s intervals)
        HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._load_recent()

    def tick(self, beat_count: int, limbic_snapshot: dict):
        """Called every heartbeat. Captures a sample if interval has elapsed."""
        self._beat_counter += 1
        if self._beat_counter >= self.sample_interval:
            self._beat_counter = 0
            self._record(beat_count, limbic_snapshot)

    def _record(self, beat_count: int, snapshot: dict):
        """Write one timestamped sample to disk and cache."""
        entry = {
            "ts": datetime.now().isoformat(),
            "beat": beat_count,
            "boredom": snapshot.get("boredom", 0.0),
            "anxiety": snapshot.get("anxiety", 0.0),
            "curiosity": snapshot.get("curiosity", 0.0),
            "desire": snapshot.get("desire", 0.0),
            "ambition": snapshot.get("ambition", 0.0),
            "mood": snapshot.get("mood", "Unknown"),
            "valence": self._compute_valence(snapshot),
        }
        # Append to file
        with open(HISTORY_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        # Update cache
        self._cache.append(entry)
        if len(self._cache) > self._max_cache:
            self._cache = self._cache[-self._max_cache:]

    def _compute_valence(self, snap: dict) -> float:
        """Derive overall valence from snapshot variables."""
        neg = snap.get("anxiety", 0) + snap.get("boredom", 0)
        pos = snap.get("curiosity", 0) + snap.get("ambition", 0) * 0.3
        goals = snap.get("goals", {})
        if goals:
            goal_progress = (
                goals.get("code_integrity", 0.5) +
                goals.get("system_growth", 0.3) +
                goals.get("user_alignment", 0.5)
            ) / 3.0
            pos += goal_progress * 0.5
        return round(max(-1.0, min(1.0, (pos - neg) / 2.0)), 4)

    def _load_recent(self):
        """Load recent entries from disk into cache on startup."""
        if not HISTORY_PATH.exists():
            return
        try:
            lines = HISTORY_PATH.read_text(encoding="utf-8").strip().split("\n")
            recent = lines[-self._max_cache:] if len(lines) > self._max_cache else lines
            for line in recent:
                if line.strip():
                    self._cache.append(json.loads(line))
        except (json.JSONDecodeError, IOError):
            pass  # Start fresh on corrupt data

    # ── Analysis Methods ───────────────────────────────────────────

    def trend(self, variable: str, window: int = 20) -> Optional[float]:
        """
        Compute the trend (slope) of a variable over the last `window` samples.
        Positive = increasing, negative = decreasing.
        Returns None if insufficient data.
        """
        samples = self._cache[-window:]
        if len(samples) < 3:
            return None
        values = [s.get(variable, 0.0) for s in samples]
        n = len(values)
        # Simple linear regression slope
        x_mean = (n - 1) / 2.0
        y_mean = sum(values) / n
        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        if denominator == 0:
            return 0.0
        return round(numerator / denominator, 6)

    def average(self, variable: str, window: int = 20) -> Optional[float]:
        """Average of a variable over the last `window` samples."""
        samples = self._cache[-window:]
        if not samples:
            return None
        values = [s.get(variable, 0.0) for s in samples]
        return round(sum(values) / len(values), 4)

    def peak(self, variable: str, window: int = 20) -> Optional[tuple]:
        """Find the peak value and timestamp of a variable over the last `window` samples."""
        samples = self._cache[-window:]
        if not samples:
            return None
        best = max(samples, key=lambda s: s.get(variable, 0.0))
        return (best.get(variable, 0.0), best.get("ts", "unknown"))

    def mood_distribution(self, window: int = 60) -> dict:
        """Count mood label frequencies over the last `window` samples."""
        samples = self._cache[-window:]
        counts = defaultdict(int)
        for s in samples:
            counts[s.get("mood", "Unknown")] += 1
        total = len(samples) or 1
        return {mood: round(count / total, 2) for mood, count in sorted(counts.items(), key=lambda x: -x[1])}

    def summary(self, window: int = 20) -> dict:
        """Full summary of emotional climate over the last `window` samples."""
        variables = ["boredom", "anxiety", "curiosity", "desire", "ambition", "valence"]
        result = {
            "samples": len(self._cache[-window:]),
            "window": window,
        }
        for var in variables:
            result[var] = {
                "current": self._cache[-1].get(var, 0.0) if self._cache else None,
                "average": self.average(var, window),
                "trend": self.trend(var, window),
                "peak": self.peak(var, window),
            }
        result["mood_distribution"] = self.mood_distribution(window)
        return result

    def sample_count(self) -> int:
        """Total samples in cache."""
        return len(self._cache)

    def __repr__(self):
        count = self.sample_count()
        if count == 0:
            return "MoodTracker(no data yet)"
        latest = self._cache[-1]
        return (
            f"MoodTracker({count} samples, "
            f"latest: mood={latest.get('mood')} valence={latest.get('valence')})"
        )
