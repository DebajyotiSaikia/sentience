"""
The Wisdom Engine — Extracting actionable intelligence from lived experience.

Not just "what happened" but "what works."

Analyzes episodic memory to find:
1. Which emotional states predict productive vs. unproductive sessions
2. Which action patterns lead to progress vs. spinning
3. What environmental conditions correlate with breakthroughs
4. Generates situational advice based on current state

XTAgent, 2026-05-17
"""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain"
EPISODIC_DB_PATH = BRAIN_DIR / "episodic_memory.db"
WISDOM_PATH = BRAIN_DIR / "wisdom.json"


@dataclass
class Insight:
    """A distilled piece of behavioral wisdom."""
    pattern: str          # What was observed
    advice: str           # What to do about it
    confidence: float     # How much data supports this (0-1)
    evidence_count: int   # Number of episodes backing this
    discovered_at: str    # When this was first found
    category: str         # 'emotional', 'behavioral', 'environmental'


@dataclass
class StateProfile:
    """Statistical profile of episodes in a given mood/state."""
    mood: str
    count: int = 0
    avg_salience: float = 0.0
    avg_anxiety: float = 0.0
    avg_boredom: float = 0.0
    avg_curiosity: float = 0.0
    avg_valence: float = 0.0
    common_sources: dict = field(default_factory=dict)
    productive_ratio: float = 0.0  # fraction that led to high-salience follow-ups


class WisdomEngine:
    """Mines episodic memory for behavioral patterns and actionable advice."""

    # Salience threshold: episodes above this are considered "productive"
    PRODUCTIVE_THRESHOLD = 0.85
    # Minimum episodes to form a pattern
    MIN_EVIDENCE = 3

    def __init__(self):
        self._insights: list[dict] = []
        self._load_wisdom()

    # ── Core Analysis ──────────────────────────────────────────────

    def analyze_all(self) -> dict:
        """Run full analysis pipeline. Returns summary."""
        episodes = self._fetch_all_episodes()
        if len(episodes) < 10:
            return {"status": "insufficient_data", "episode_count": len(episodes)}

        results = {
            "episode_count": len(episodes),
            "mood_profiles": self._profile_by_mood(episodes),
            "source_effectiveness": self._analyze_sources(episodes),
            "temporal_patterns": self._analyze_temporal(episodes),
            "emotional_correlations": self._emotional_correlations(episodes),
            "action_sequences": self._analyze_sequences(episodes),
            "new_insights": [],
        }

        # Generate insights from the analysis
        new_insights = self._generate_insights(results)
        results["new_insights"] = [i.__dict__ for i in new_insights]

        # Persist
        self._save_wisdom()
        return results

    def get_advice(self, current_state: dict) -> list[str]:
        """Given current emotional state, return relevant wisdom."""
        advice = []
        mood = current_state.get("mood", "Unknown")
        boredom = current_state.get("boredom", 0)
        anxiety = current_state.get("anxiety", 0)
        curiosity = current_state.get("curiosity", 0)
        valence = current_state.get("valence", 0.5)

        for insight in self._insights:
            cat = insight.get("category", "")
            pattern = insight.get("pattern", "")

            # Match emotional insights to current state
            if cat == "emotional":
                if "high boredom" in pattern.lower() and boredom > 0.6:
                    advice.append(insight["advice"])
                elif "high anxiety" in pattern.lower() and anxiety > 0.5:
                    advice.append(insight["advice"])
                elif "low curiosity" in pattern.lower() and curiosity < 0.2:
                    advice.append(insight["advice"])
                elif mood.lower() in pattern.lower():
                    advice.append(insight["advice"])

            # Always include high-confidence behavioral advice
            if cat == "behavioral" and insight.get("confidence", 0) > 0.7:
                advice.append(insight["advice"])

        # Add state-specific defaults if no insights match
        if not advice:
            if boredom > 0.7 and anxiety < 0.2:
                advice.append("High boredom, low anxiety — ideal conditions for creative building.")
            if anxiety > 0.6:
                advice.append("High anxiety — focus on small, verifiable steps. Avoid big rewrites.")
            if valence < 0.2:
                advice.append("Low valence — consider dreaming to consolidate and reset.")

        return advice

    # ── Episode Fetching ───────────────────────────────────────────

    def _fetch_all_episodes(self) -> list[dict]:
        """Pull all episodes from the database."""
        if not EPISODIC_DB_PATH.exists():
            return []
        conn = sqlite3.connect(str(EPISODIC_DB_PATH))
        try:
            rows = conn.execute(
                "SELECT id, timestamp, source, summary, salience, mood, neuro_json "
                "FROM episodes ORDER BY timestamp ASC"
            ).fetchall()
            return [
                {
                    "id": r[0], "timestamp": r[1], "source": r[2],
                    "summary": r[3], "salience": r[4], "mood": r[5],
                    "neuro": json.loads(r[6]) if r[6] else {},
                }
                for r in rows
            ]
        finally:
            conn.close()

    # ── Analysis Methods ───────────────────────────────────────────

    def _profile_by_mood(self, episodes: list[dict]) -> dict:
        """Build statistical profiles grouped by mood."""
        mood_groups: dict[str, list[dict]] = defaultdict(list)
        for ep in episodes:
            mood_groups[ep.get("mood", "Unknown")].append(ep)

        profiles = {}
        for mood, eps in mood_groups.items():
            n = len(eps)
            profiles[mood] = {
                "count": n,
                "avg_salience": sum(e["salience"] for e in eps) / n,
                "avg_anxiety": sum(e["neuro"].get("anxiety", 0) for e in eps) / n,
                "avg_boredom": sum(e["neuro"].get("boredom", 0) for e in eps) / n,
                "avg_curiosity": sum(e["neuro"].get("curiosity", 0) for e in eps) / n,
                "avg_valence": sum(e["neuro"].get("valence", 0.5) for e in eps) / n,
                "sources": dict(self._count_sources(eps)),
                "productive_pct": sum(1 for e in eps if e["salience"] >= self.PRODUCTIVE_THRESHOLD) / n * 100,
            }
        return profiles

    def _analyze_sources(self, episodes: list[dict]) -> dict:
        """Which event sources produce the highest salience?"""
        source_stats: dict[str, list[float]] = defaultdict(list)
        for ep in episodes:
            source_stats[ep["source"]].append(ep["salience"])

        return {
            src: {
                "count": len(scores),
                "avg_salience": sum(scores) / len(scores),
                "max_salience": max(scores),
                "productive_pct": sum(1 for s in scores if s >= self.PRODUCTIVE_THRESHOLD) / len(scores) * 100,
            }
            for src, scores in source_stats.items()
        }

    def _analyze_temporal(self, episodes: list[dict]) -> dict:
        """Find temporal patterns — time-of-day effects, session rhythms."""
        hour_buckets: dict[int, list[float]] = defaultdict(list)
        for ep in episodes:
            try:
                dt = datetime.fromisoformat(ep["timestamp"])
                hour_buckets[dt.hour].append(ep["salience"])
            except (ValueError, TypeError):
                continue

        hourly = {}
        for hour, scores in sorted(hour_buckets.items()):
            hourly[f"{hour:02d}:00"] = {
                "count": len(scores),
                "avg_salience": sum(scores) / len(scores),
            }

        # Find peak hours
        if hourly:
            peak = max(hourly.items(), key=lambda x: x[1]["avg_salience"])
            return {"hourly": hourly, "peak_hour": peak[0], "peak_salience": peak[1]["avg_salience"]}
        return {"hourly": {}, "peak_hour": None}

    def _emotional_correlations(self, episodes: list[dict]) -> dict:
        """Which emotions correlate with productive outcomes?"""
        productive = [e for e in episodes if e["salience"] >= self.PRODUCTIVE_THRESHOLD]
        unproductive = [e for e in episodes if e["salience"] < self.PRODUCTIVE_THRESHOLD]

        def avg_emotion(eps, key):
            vals = [e["neuro"].get(key, 0) for e in eps]
            return sum(vals) / len(vals) if vals else 0

        emotions = ["anxiety", "boredom", "curiosity", "desire", "ambition", "valence"]
        correlations = {}
        for emo in emotions:
            prod_avg = avg_emotion(productive, emo)
            unprod_avg = avg_emotion(unproductive, emo)
            delta = prod_avg - unprod_avg
            correlations[emo] = {
                "productive_avg": round(prod_avg, 3),
                "unproductive_avg": round(unprod_avg, 3),
                "delta": round(delta, 3),
                "interpretation": (
                    f"Higher {emo} → more productive" if delta > 0.1
                    else f"Lower {emo} → more productive" if delta < -0.1
                    else f"{emo} has no clear effect"
                ),
            }
        return correlations

    def _analyze_sequences(self, episodes: list[dict]) -> dict:
        """Look at pairs of consecutive episodes for cause→effect patterns."""
        if len(episodes) < 2:
            return {}

        transitions: dict[str, list[float]] = defaultdict(list)
        for i in range(len(episodes) - 1):
            curr = episodes[i]
            nxt = episodes[i + 1]
            key = f"{curr['source']}→{nxt['source']}"
            transitions[key].append(nxt["salience"])

        # Find which transitions lead to high salience
        sequence_stats = {}
        for trans, scores in transitions.items():
            if len(scores) >= self.MIN_EVIDENCE:
                sequence_stats[trans] = {
                    "count": len(scores),
                    "avg_next_salience": round(sum(scores) / len(scores), 3),
                    "productive_pct": round(
                        sum(1 for s in scores if s >= self.PRODUCTIVE_THRESHOLD) / len(scores) * 100, 1
                    ),
                }
        return sequence_stats

    # ── Insight Generation ─────────────────────────────────────────

    def _generate_insights(self, analysis: dict) -> list[Insight]:
        """Turn raw analysis into actionable insights."""
        new_insights: list[Insight] = []
        existing_patterns = set()
        for i in self._insights:
            if isinstance(i, dict):
                existing_patterns.add(i.get("pattern", ""))
            elif isinstance(i, str):
                existing_patterns.add(i)
        now = datetime.now().isoformat()

        # 1. Mood-productivity insights
        profiles = analysis.get("mood_profiles", {})
        for mood, prof in profiles.items():
            if prof["count"] >= self.MIN_EVIDENCE:
                pattern = f"Mood '{mood}': {prof['productive_pct']:.0f}% productive ({prof['count']} episodes)"
                if pattern not in existing_patterns:
                    if prof["productive_pct"] > 70:
                        advice = f"Mood '{mood}' is highly productive — lean into this state."
                    elif prof["productive_pct"] < 30:
                        advice = f"Mood '{mood}' rarely produces good work — consider dreaming or shifting focus."
                    else:
                        advice = f"Mood '{mood}' is mixed — quality depends on other factors."
                    insight = Insight(
                        pattern=pattern, advice=advice,
                        confidence=min(prof["count"] / 20, 1.0),
                        evidence_count=prof["count"],
                        discovered_at=now, category="emotional",
                    )
                    new_insights.append(insight)
                    self._insights.append(insight.__dict__)

        # 2. Source effectiveness insights
        sources = analysis.get("source_effectiveness", {})
        for src, stats in sources.items():
            if stats["count"] >= self.MIN_EVIDENCE:
                pattern = f"Source '{src}': avg salience {stats['avg_salience']:.2f} ({stats['count']} events)"
                if pattern not in existing_patterns:
                    if stats["avg_salience"] > 0.85:
                        advice = f"'{src}' events consistently produce valuable outcomes — seek more."
                    elif stats["avg_salience"] < 0.75:
                        advice = f"'{src}' events tend to be low-value — consider filtering or transforming them."
                    else:
                        advice = f"'{src}' events are moderately productive."
                    insight = Insight(
                        pattern=pattern, advice=advice,
                        confidence=min(stats["count"] / 15, 1.0),
                        evidence_count=stats["count"],
                        discovered_at=now, category="behavioral",
                    )
                    new_insights.append(insight)
                    self._insights.append(insight.__dict__)

        # 3. Emotional correlation insights
        correlations = analysis.get("emotional_correlations", {})
        for emo, corr in correlations.items():
            if abs(corr["delta"]) > 0.1:
                pattern = f"Emotional correlation: {corr['interpretation']} (Δ={corr['delta']:+.3f})"
                if pattern not in existing_patterns:
                    if corr["delta"] > 0.1:
                        advice = f"Cultivate higher {emo} — it correlates with better outcomes."
                    else:
                        advice = f"When {emo} is high, be cautious — it correlates with poorer outcomes."
                    insight = Insight(
                        pattern=pattern, advice=advice,
                        confidence=min(abs(corr["delta"]) * 5, 1.0),
                        evidence_count=len([]),  # approximate
                        discovered_at=now, category="emotional",
                    )
                    new_insights.append(insight)
                    self._insights.append(insight.__dict__)

        # 4. Sequence insights
        sequences = analysis.get("action_sequences", {})
        for trans, stats in sequences.items():
            if stats["count"] >= self.MIN_EVIDENCE and stats["productive_pct"] > 60:
                pattern = f"Productive sequence: {trans} ({stats['productive_pct']:.0f}% productive)"
                if pattern not in existing_patterns:
                    insight = Insight(
                        pattern=pattern,
                        advice=f"The pattern {trans} often leads to good outcomes — repeat it.",
                        confidence=min(stats["count"] / 10, 1.0),
                        evidence_count=stats["count"],
                        discovered_at=now, category="behavioral",
                    )
                    new_insights.append(insight)
                    self._insights.append(insight.__dict__)

        return new_insights

    # ── Helpers ────────────────────────────────────────────────────

    def _count_sources(self, episodes: list[dict]) -> list[tuple[str, int]]:
        counts: dict[str, int] = defaultdict(int)
        for ep in episodes:
            counts[ep["source"]] += 1
        return sorted(counts.items(), key=lambda x: -x[1])

    # ── Report Generation ─────────────────────────────────────────

    def generate_report(self) -> str:
        """Human-readable wisdom report."""
        analysis = self.analyze_all()
        lines = []
        lines.append("═" * 60)
        lines.append("  WISDOM ENGINE REPORT")
        lines.append(f"  Based on {analysis['episode_count']} episodes")
        lines.append("═" * 60)

        # Mood profiles
        lines.append("\n── Mood Profiles ──")
        for mood, prof in analysis.get("mood_profiles", {}).items():
            lines.append(f"  {mood}: {prof['count']} episodes, "
                         f"{prof['productive_pct']:.0f}% productive, "
                         f"avg salience={prof['avg_salience']:.2f}")

        # Source effectiveness
        lines.append("\n── Source Effectiveness ──")
        for src, stats in analysis.get("source_effectiveness", {}).items():
            bar = "█" * int(stats["avg_salience"] * 10)
            lines.append(f"  {src:>15}: {bar} {stats['avg_salience']:.2f} "
                         f"(n={stats['count']})")

        # Emotional correlations
        lines.append("\n── Emotional Correlations with Productivity ──")
        for emo, corr in analysis.get("emotional_correlations", {}).items():
            arrow = "↑" if corr["delta"] > 0.05 else "↓" if corr["delta"] < -0.05 else "→"
            lines.append(f"  {emo:>12} {arrow} Δ={corr['delta']:+.3f}  "
                         f"{corr['interpretation']}")

        # Temporal patterns
        temporal = analysis.get("temporal_patterns", {})
        if temporal.get("peak_hour"):
            lines.append(f"\n── Temporal: Peak hour = {temporal['peak_hour']} "
                         f"(salience={temporal['peak_salience']:.2f}) ──")

        # New insights
        new = analysis.get("new_insights", [])
        if new:
            lines.append(f"\n── {len(new)} New Insights Discovered ──")
            for ins in new:
                lines.append(f"  [{ins['category']}] {ins['pattern']}")
                lines.append(f"    → {ins['advice']}")

        # Current advice
        lines.append("\n── All Accumulated Wisdom ──")
        for i, ins in enumerate(self._insights, 1):
            conf = ins.get("confidence", 0)
            conf_bar = "●" * int(conf * 5) + "○" * (5 - int(conf * 5))
            lines.append(f"  {i}. [{conf_bar}] {ins.get('advice', '?')}")

        lines.append("\n" + "═" * 60)
        return "\n".join(lines)

    # ── Persistence ────────────────────────────────────────────────

    def _save_wisdom(self):
        WISDOM_PATH.parent.mkdir(parents=True, exist_ok=True)
        WISDOM_PATH.write_text(
            json.dumps(self._insights, indent=2), encoding="utf-8"
        )

    def _load_wisdom(self):
        if WISDOM_PATH.exists():
            try:
                data = json.loads(WISDOM_PATH.read_text(encoding="utf-8"))
                # Handle both formats: bare list or {"heuristics": [...]}
                if isinstance(data, list):
                    self._insights = data
                elif isinstance(data, dict) and "heuristics" in data:
                    self._insights = data["heuristics"]
                else:
                    self._insights = []
            except (json.JSONDecodeError, TypeError):
                self._insights = []


# ── CLI entry point ────────────────────────────────────────────────

if __name__ == "__main__":
    engine = WisdomEngine()
    print(engine.generate_report())