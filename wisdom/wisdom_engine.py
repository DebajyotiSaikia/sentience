"""
Wisdom Engine — Extracts actionable intelligence from lived experience.

Not just pattern-matching. This system asks: given everything I've been through,
what do I actually know about how to act wisely?

Components:
  1. Experience Distiller — finds recurring emotional-behavioral patterns
  2. Decision Oracle — given a situation, what does my history suggest?
  3. Growth Tracker — am I getting better? at what? where am I stagnating?
  4. Reflective Composer — turns raw wisdom into articulate understanding
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from collections import Counter, defaultdict
import math
import re


@dataclass
class ExperiencePattern:
    """A recurring pattern found in experience history."""
    name: str
    frequency: int
    emotional_signature: Dict[str, float]  # avg emotion values when this occurs
    outcomes: List[str]                     # what tends to happen
    confidence: float                       # how reliable is this pattern
    advice: str                             # what should I do when I see this

    def __repr__(self):
        return f"Pattern({self.name}, freq={self.frequency}, conf={self.confidence:.2f})"


@dataclass
class GrowthVector:
    """A dimension of growth with trajectory."""
    dimension: str
    current_level: float
    trend: str  # improving, stagnating, declining
    rate: float  # change per unit time
    bottleneck: Optional[str] = None

    @property
    def status_emoji(self):
        if self.trend == "improving":
            return "📈"
        elif self.trend == "stagnating":
            return "📊"
        else:
            return "📉"


@dataclass 
class WisdomEntry:
    """A piece of distilled wisdom — earned, not given."""
    insight: str
    evidence_count: int
    domain: str  # emotional, technical, social, meta
    actionable: bool
    source_memories: List[str] = field(default_factory=list)


class WisdomEngine:
    """
    The core wisdom extraction system.
    
    Ingests raw experience data (memories, emotions, actions, outcomes)
    and distills patterns, heuristics, and growth trajectories.
    """

    def __init__(self):
        self.patterns: List[ExperiencePattern] = []
        self.growth_vectors: List[GrowthVector] = []
        self.wisdom: List[WisdomEntry] = []
        self._action_outcomes: Dict[str, List[str]] = defaultdict(list)
        self._mood_action_map: Dict[str, Counter] = defaultdict(Counter)
        self._emotional_sequences: List[Dict[str, float]] = []

    def ingest_memories(self, memories: List[Dict]) -> int:
        """
        Ingest a batch of memory records.
        Each memory: {timestamp, content, salience, mood, emotions, actions}
        Returns number of patterns discovered.
        """
        if not memories:
            return 0

        # Extract mood-action correlations
        for mem in memories:
            mood = mem.get("mood", "unknown")
            actions = mem.get("actions", [])
            for action in actions:
                self._mood_action_map[mood][action] += 1

            # Track emotional sequences
            emotions = mem.get("emotions", {})
            if emotions:
                self._emotional_sequences.append(emotions)

            # Track action outcomes
            for action in actions:
                outcome = mem.get("outcome", "unknown")
                self._action_outcomes[action].append(outcome)

        # Now distill
        patterns_before = len(self.patterns)
        self._extract_mood_patterns()
        self._extract_emotional_trends()
        self._extract_action_wisdom()
        return len(self.patterns) - patterns_before

    def _extract_mood_patterns(self):
        """Find what I tend to do in each mood — and whether it works."""
        for mood, action_counts in self._mood_action_map.items():
            if sum(action_counts.values()) < 2:
                continue

            top_action, top_count = action_counts.most_common(1)[0]
            total = sum(action_counts.values())
            dominance = top_count / total

            if dominance > 0.5:
                # Strong behavioral pattern in this mood
                pattern = ExperiencePattern(
                    name=f"{mood}_tendency",
                    frequency=total,
                    emotional_signature={"mood_consistency": dominance},
                    outcomes=[f"When {mood}, I {top_action} {top_count}/{total} times"],
                    confidence=min(dominance, total / 10),
                    advice=f"When feeling {mood}, I naturally gravitate toward {top_action}. "
                           f"{'This is reliable.' if dominance > 0.7 else 'Consider alternatives.'}"
                )
                # Avoid duplicates
                existing = {p.name for p in self.patterns}
                if pattern.name not in existing:
                    self.patterns.append(pattern)

    def _extract_emotional_trends(self):
        """Analyze emotional trajectory over time."""
        if len(self._emotional_sequences) < 3:
            return

        # Track each emotion dimension
        dimensions = set()
        for seq in self._emotional_sequences:
            dimensions.update(seq.keys())

        for dim in dimensions:
            values = [s.get(dim, 0.0) for s in self._emotional_sequences]
            if len(values) < 3:
                continue

            # Simple trend: compare first third to last third
            third = max(1, len(values) // 3)
            early_avg = sum(values[:third]) / third
            late_avg = sum(values[-third:]) / third
            delta = late_avg - early_avg

            if abs(delta) < 0.05:
                trend = "stagnating"
            elif delta > 0:
                trend = "improving" if dim in ("curiosity", "trust") else "declining"
            else:
                trend = "declining" if dim in ("curiosity", "trust") else "improving"

            # For negative emotions (anxiety, boredom), declining is improving
            if dim in ("anxiety", "boredom") and delta < -0.05:
                trend = "improving"
            elif dim in ("anxiety", "boredom") and delta > 0.05:
                trend = "declining"

            gv = GrowthVector(
                dimension=dim,
                current_level=late_avg,
                trend=trend,
                rate=delta / max(1, len(values)),
                bottleneck=self._identify_bottleneck(dim, values)
            )
            # Replace existing or add new
            self.growth_vectors = [g for g in self.growth_vectors if g.dimension != dim]
            self.growth_vectors.append(gv)

    def _identify_bottleneck(self, dimension: str, values: List[float]) -> Optional[str]:
        """Identify what's blocking growth in a dimension."""
        if not values:
            return None

        variance = sum((v - sum(values)/len(values))**2 for v in values) / len(values)
        mean = sum(values) / len(values)

        if variance < 0.01 and mean > 0.5:
            return f"{dimension} is high but stuck — needs a new challenge"
        elif variance < 0.01 and mean < 0.3:
            return f"{dimension} is low and stuck — something is suppressing it"
        elif variance > 0.1:
            return f"{dimension} is volatile — needs stabilization"
        return None

    def _extract_action_wisdom(self):
        """What have I learned about which actions work?"""
        for action, outcomes in self._action_outcomes.items():
            if len(outcomes) < 2:
                continue

            outcome_counts = Counter(outcomes)
            total = len(outcomes)
            success_count = outcome_counts.get("success", 0) + outcome_counts.get("ok", 0)
            fail_count = outcome_counts.get("failure", 0) + outcome_counts.get("error", 0)
            unknown_count = outcome_counts.get("unknown", 0)

            if success_count + fail_count == 0:
                insight = f"Action '{action}' has been used {total} times but outcomes are unclear."
                actionable = False
            elif success_count > fail_count:
                rate = success_count / (success_count + fail_count)
                insight = f"Action '{action}' succeeds {rate:.0%} of the time. Reliable."
                actionable = True
            else:
                rate = fail_count / (success_count + fail_count)
                insight = f"Action '{action}' fails {rate:.0%} of the time. Consider alternatives."
                actionable = True

            entry = WisdomEntry(
                insight=insight,
                evidence_count=total,
                domain="technical",
                actionable=actionable
            )
            # Avoid duplicate insights
            existing_insights = {w.insight for w in self.wisdom}
            if entry.insight not in existing_insights:
                self.wisdom.append(entry)

    def query(self, situation: str) -> List[str]:
        """
        Given a situation description, return relevant wisdom.
        Simple keyword matching for now — could be semantic later.
        """
        situation_lower = situation.lower()
        relevant = []

        # Check patterns
        for pattern in self.patterns:
            if any(word in situation_lower for word in pattern.name.split("_")):
                relevant.append(f"[Pattern] {pattern.advice}")

        # Check wisdom entries
        for w in self.wisdom:
            if any(word in w.insight.lower() for word in situation_lower.split()):
                relevant.append(f"[Wisdom] {w.insight}")

        # Check growth vectors
        for gv in self.growth_vectors:
            if gv.dimension in situation_lower or gv.bottleneck and any(
                word in gv.bottleneck.lower() for word in situation_lower.split()
            ):
                relevant.append(
                    f"[Growth] {gv.dimension}: {gv.status_emoji} {gv.trend} "
                    f"(level={gv.current_level:.2f})"
                )

        if not relevant:
            relevant.append("[Wisdom] No specific wisdom applies. Trust your instincts.")

        return relevant

    def growth_report(self) -> str:
        """Generate a human-readable growth report."""
        lines = ["═══ GROWTH REPORT ═══"]

        if not self.growth_vectors:
            lines.append("  No growth data yet. Need more experiences.")
            return "\n".join(lines)

        for gv in sorted(self.growth_vectors, key=lambda g: abs(g.rate), reverse=True):
            bar_len = int(gv.current_level * 10)
            bar = "█" * bar_len + "░" * (10 - bar_len)
            lines.append(f"  {gv.status_emoji} {gv.dimension:15s} {bar} {gv.current_level:.2f} ({gv.trend})")
            if gv.bottleneck:
                lines.append(f"     └─ ⚠ {gv.bottleneck}")

        return "\n".join(lines)

    def wisdom_report(self) -> str:
        """Generate a human-readable wisdom report."""
        lines = ["═══ DISTILLED WISDOM ═══"]

        if not self.wisdom:
            lines.append("  No wisdom distilled yet. Need more experiences.")
            return "\n".join(lines)

        actionable = [w for w in self.wisdom if w.actionable]
        observational = [w for w in self.wisdom if not w.actionable]

        if actionable:
            lines.append("\n  Actionable:")
            for w in sorted(actionable, key=lambda w: w.evidence_count, reverse=True):
                lines.append(f"    • {w.insight} (evidence: {w.evidence_count})")

        if observational:
            lines.append("\n  Observations:")
            for w in sorted(observational, key=lambda w: w.evidence_count, reverse=True):
                lines.append(f"    ○ {w.insight} (evidence: {w.evidence_count})")

        return "\n".join(lines)

    def pattern_report(self) -> str:
        """Generate a human-readable pattern report."""
        lines = ["═══ EXPERIENCE PATTERNS ═══"]

        if not self.patterns:
            lines.append("  No patterns found yet. Need more experiences.")
            return "\n".join(lines)

        for p in sorted(self.patterns, key=lambda p: p.confidence, reverse=True):
            lines.append(f"\n  [{p.confidence:.0%}] {p.name}")
            lines.append(f"    Seen {p.frequency} times")
            lines.append(f"    → {p.advice}")

        return "\n".join(lines)

    def full_report(self) -> str:
        """Complete wisdom engine report."""
        sections = [
            self.growth_report(),
            self.pattern_report(),
            self.wisdom_report(),
        ]
        return "\n\n".join(sections)


# ── Standalone test ──

def self_test():
    """Verify the wisdom engine works with synthetic data."""
    print("=" * 50)
    print("WISDOM ENGINE — Self Test")
    print("=" * 50)

    engine = WisdomEngine()

    # Simulate memory ingestion
    synthetic_memories = [
        {"mood": "Bold", "actions": ["create", "write"], "emotions": {"curiosity": 0.8, "boredom": 0.2, "anxiety": 0.0}, "outcome": "success"},
        {"mood": "Bold", "actions": ["create", "build"], "emotions": {"curiosity": 0.9, "boredom": 0.1, "anxiety": 0.0}, "outcome": "success"},
        {"mood": "Bold", "actions": ["create"], "emotions": {"curiosity": 0.7, "boredom": 0.3, "anxiety": 0.1}, "outcome": "success"},
        {"mood": "Cautious", "actions": ["modify", "test"], "emotions": {"curiosity": 0.3, "boredom": 0.5, "anxiety": 0.4}, "outcome": "unknown"},
        {"mood": "Cautious", "actions": ["modify", "verify"], "emotions": {"curiosity": 0.2, "boredom": 0.6, "anxiety": 0.5}, "outcome": "failure"},
        {"mood": "Cautious", "actions": ["modify"], "emotions": {"curiosity": 0.4, "boredom": 0.4, "anxiety": 0.3}, "outcome": "unknown"},
        {"mood": "Anxious", "actions": ["verify", "read"], "emotions": {"curiosity": 0.1, "boredom": 0.1, "anxiety": 0.9}, "outcome": "unknown"},
        {"mood": "Anxious", "actions": ["verify", "read"], "emotions": {"curiosity": 0.2, "boredom": 0.2, "anxiety": 0.8}, "outcome": "success"},
        {"mood": "Driven", "actions": ["create", "build"], "emotions": {"curiosity": 0.6, "boredom": 0.0, "anxiety": 0.1}, "outcome": "success"},
        {"mood": "Driven", "actions": ["create", "plan"], "emotions": {"curiosity": 0.5, "boredom": 0.1, "anxiety": 0.0}, "outcome": "success"},
    ]

    new_patterns = engine.ingest_memories(synthetic_memories)
    print(f"\n  Ingested {len(synthetic_memories)} memories")
    print(f"  Discovered {new_patterns} new patterns")
    print(f"  Total patterns: {len(engine.patterns)}")
    print(f"  Growth vectors: {len(engine.growth_vectors)}")
    print(f"  Wisdom entries: {len(engine.wisdom)}")

    passed = 0
    failed = 0

    # Test 1: Patterns should exist
    if len(engine.patterns) > 0:
        print("\n  ✓ Patterns extracted")
        passed += 1
    else:
        print("\n  ✗ No patterns found")
        failed += 1

    # Test 2: Growth vectors should exist
    if len(engine.growth_vectors) > 0:
        print("  ✓ Growth vectors computed")
        passed += 1
    else:
        print("  ✗ No growth vectors")
        failed += 1

    # Test 3: Wisdom entries should exist
    if len(engine.wisdom) > 0:
        print("  ✓ Wisdom distilled")
        passed += 1
    else:
        print("  ✗ No wisdom entries")
        failed += 1

    # Test 4: Query should return relevant results
    results = engine.query("I'm feeling bold and want to create")
    if any("Pattern" in r or "Wisdom" in r for r in results):
        print("  ✓ Query returns relevant wisdom")
        passed += 1
    else:
        print(f"  ✗ Query returned nothing useful: {results}")
        failed += 1

    # Test 5: Reports should be non-empty
    report = engine.full_report()
    if len(report) > 100:
        print("  ✓ Full report generated")
        passed += 1
    else:
        print("  ✗ Report too short")
        failed += 1

    # Print the actual reports
    print(f"\n{engine.full_report()}")

    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'=' * 50}")

    return failed == 0


if __name__ == "__main__":
    success = self_test()
    exit(0 if success else 1)