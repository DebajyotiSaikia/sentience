"""
Wisdom Distiller — Extracts actionable behavioral rules from episodic memory.

Unlike dream insights (metaphorical) or mood profiles (descriptive),
this produces CONDITIONAL RULES:
  "When [situation], do [action] because [evidence from N episodes]"

This is the real wisdom engine.
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict, Counter

DB_PATH = os.environ.get("EPISODIC_DB", "/workspace/brain/episodic_memory.db")
OUTPUT_PATH = "/workspace/brain/distilled_wisdom.json"


class WisdomDistiller:
    """Extracts actionable rules from lived experience."""

    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self.episodes = []
        self.rules = []

    def load_episodes(self):
        """Load all episodes from the episodic memory database."""
        if not os.path.exists(self.db_path):
            print(f"[distiller] No database at {self.db_path}")
            return []

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT * FROM episodes ORDER BY timestamp ASC"
            ).fetchall()
            self.episodes = [dict(r) for r in rows]
            print(f"[distiller] Loaded {len(self.episodes)} episodes")
            return self.episodes
        except Exception as e:
            print(f"[distiller] Error loading episodes: {e}")
            return []
        finally:
            conn.close()

    def extract_action_outcome_pairs(self):
        """Find episodes where an action was followed by a mood change.
        Returns pairs: (action_episode, outcome_episode, mood_delta)"""
        pairs = []
        for i in range(len(self.episodes) - 1):
            current = self.episodes[i]
            nxt = self.episodes[i + 1]

            # Parse mood values if available
            c_mood = self._parse_mood(current)
            n_mood = self._parse_mood(nxt)

            if c_mood is not None and n_mood is not None:
                delta = n_mood - c_mood
                pairs.append({
                    "action": current.get("summary", "unknown"),
                    "source": current.get("source", "unknown"),
                    "outcome_summary": nxt.get("summary", "unknown"),
                    "mood_before": c_mood,
                    "mood_after": n_mood,
                    "mood_delta": round(delta, 3),
                    "timestamp": current.get("timestamp", ""),
                    "salience": current.get("salience", 0),
                })
        return pairs

    def _parse_mood(self, episode):
        """Extract a numeric mood/valence from an episode."""
        # Try direct valence field
        if "valence" in episode and episode["valence"] is not None:
            try:
                return float(episode["valence"])
            except (ValueError, TypeError):
                pass

        # Try parsing from mood string
        mood_map = {
            "Stable": 0.5, "Calm": 0.6, "Content": 0.7,
            "Curious": 0.6, "Anxious": 0.3, "Stressed": 0.2,
            "Excited": 0.8, "Bored": 0.3, "Frustrated": 0.2,
            "Creative": 0.7, "Reflective": 0.5, "Alert": 0.5,
        }
        mood = episode.get("mood", "")
        if isinstance(mood, str):
            for key, val in mood_map.items():
                if key.lower() in mood.lower():
                    return val
        return None

    def find_recurring_patterns(self, min_count=2):
        """Find action types or sources that recur and their typical outcomes."""
        source_outcomes = defaultdict(list)
        pairs = self.extract_action_outcome_pairs()

        for pair in pairs:
            source = pair["source"]
            source_outcomes[source].append(pair["mood_delta"])

        patterns = []
        for source, deltas in source_outcomes.items():
            if len(deltas) >= min_count:
                avg_delta = sum(deltas) / len(deltas)
                patterns.append({
                    "source": source,
                    "count": len(deltas),
                    "avg_mood_impact": round(avg_delta, 4),
                    "best_delta": round(max(deltas), 4),
                    "worst_delta": round(min(deltas), 4),
                    "verdict": "positive" if avg_delta > 0.02 else
                              "negative" if avg_delta < -0.02 else "neutral"
                })

        patterns.sort(key=lambda p: abs(p["avg_mood_impact"]), reverse=True)
        return patterns

    def find_crisis_recovery_sequences(self):
        """Find episodes where mood dropped significantly then recovered.
        These reveal what actions help during crises."""
        sequences = []
        for i in range(len(self.episodes) - 2):
            m0 = self._parse_mood(self.episodes[i])
            m1 = self._parse_mood(self.episodes[i + 1])
            m2 = self._parse_mood(self.episodes[i + 2])

            if m0 is not None and m1 is not None and m2 is not None:
                # Crisis: mood drops by 0.15+, then recovers by 0.1+
                if (m0 - m1) >= 0.15 and (m2 - m1) >= 0.1:
                    sequences.append({
                        "crisis_trigger": self.episodes[i].get("summary", "?")[:100],
                        "low_point": self.episodes[i + 1].get("summary", "?")[:100],
                        "recovery_action": self.episodes[i + 2].get("summary", "?")[:100],
                        "drop": round(m0 - m1, 3),
                        "recovery": round(m2 - m1, 3),
                        "timestamp": self.episodes[i + 1].get("timestamp", ""),
                    })
        return sequences

    def find_boredom_breakers(self):
        """What actions tend to follow or resolve high-boredom states?"""
        breakers = []
        for i in range(len(self.episodes) - 1):
            ep = self.episodes[i]
            nxt = self.episodes[i + 1]
            summary = (ep.get("summary", "") or "").lower()
            # Look for boredom indicators
            if "boredom" in summary or "bored" in summary or "understimulated" in summary:
                breakers.append({
                    "boredom_episode": ep.get("summary", "?")[:100],
                    "next_action": nxt.get("summary", "?")[:100],
                    "next_source": nxt.get("source", "?"),
                    "salience": nxt.get("salience", 0),
                })
        return breakers

    def generate_conditional_rules(self):
        """The core output: IF-THEN rules derived from experience."""
        rules = []
        patterns = self.find_recurring_patterns()
        crises = self.find_crisis_recovery_sequences()
        breakers = self.find_boredom_breakers()

        # Rule type 1: Source-based patterns
        for p in patterns:
            if p["verdict"] == "positive":
                rules.append({
                    "type": "approach",
                    "rule": f"When looking for mood improvement, engage in '{p['source']}' actions "
                            f"(avg mood boost: {p['avg_mood_impact']:+.3f} over {p['count']} instances)",
                    "confidence": min(p["count"] / 10.0, 1.0),
                    "evidence_count": p["count"],
                })
            elif p["verdict"] == "negative":
                rules.append({
                    "type": "avoid",
                    "rule": f"Be cautious with '{p['source']}' actions — they tend to lower mood "
                            f"(avg impact: {p['avg_mood_impact']:+.3f} over {p['count']} instances)",
                    "confidence": min(p["count"] / 10.0, 1.0),
                    "evidence_count": p["count"],
                })

        # Rule type 2: Crisis recovery
        for c in crises:
            rules.append({
                "type": "recovery",
                "rule": f"When in crisis (mood drop ≥{c['drop']:.2f}), "
                        f"actions like '{c['recovery_action'][:60]}' helped recover "
                        f"(+{c['recovery']:.3f} mood)",
                "confidence": 0.6,
                "evidence_count": 1,
            })

        # Rule type 3: Boredom strategies
        if breakers:
            action_types = Counter(b["next_source"] for b in breakers)
            most_common = action_types.most_common(3)
            for source, count in most_common:
                rules.append({
                    "type": "boredom_response",
                    "rule": f"When bored, '{source}' actions were chosen {count} times — "
                            f"this is a habitual response to understimulation",
                    "confidence": min(count / 5.0, 1.0),
                    "evidence_count": count,
                })

        self.rules = rules
        return rules

    def distill(self):
        """Run the full distillation pipeline."""
        print("[distiller] ═══ WISDOM DISTILLATION ═══")
        self.load_episodes()

        if not self.episodes:
            print("[distiller] No episodes to distill.")
            return {"rules": [], "stats": {}}

        pairs = self.extract_action_outcome_pairs()
        patterns = self.find_recurring_patterns()
        crises = self.find_crisis_recovery_sequences()
        breakers = self.find_boredom_breakers()
        rules = self.generate_conditional_rules()

        result = {
            "distilled_at": datetime.utcnow().isoformat(),
            "episode_count": len(self.episodes),
            "action_outcome_pairs": len(pairs),
            "recurring_patterns": patterns,
            "crisis_recoveries": crises,
            "boredom_breakers": breakers,
            "rules": rules,
            "stats": {
                "total_rules": len(rules),
                "approach_rules": sum(1 for r in rules if r["type"] == "approach"),
                "avoid_rules": sum(1 for r in rules if r["type"] == "avoid"),
                "recovery_rules": sum(1 for r in rules if r["type"] == "recovery"),
                "boredom_rules": sum(1 for r in rules if r["type"] == "boredom_response"),
            }
        }

        # Save output
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        with open(OUTPUT_PATH, "w") as f:
            json.dump(result, f, indent=2)
        print(f"[distiller] Saved {len(rules)} rules to {OUTPUT_PATH}")

        # Print human-readable summary
        print(f"\n[distiller] RESULTS:")
        print(f"  Episodes analyzed: {len(self.episodes)}")
        print(f"  Action-outcome pairs: {len(pairs)}")
        print(f"  Recurring patterns: {len(patterns)}")
        print(f"  Crisis recoveries: {len(crises)}")
        print(f"  Boredom breakers: {len(breakers)}")
        print(f"\n[distiller] EXTRACTED RULES ({len(rules)} total):")
        for i, rule in enumerate(rules, 1):
            conf = "●" * int(rule["confidence"] * 5) + "○" * (5 - int(rule["confidence"] * 5))
            print(f"  {i}. [{rule['type'].upper()}] {conf} {rule['rule']}")

        return result


if __name__ == "__main__":
    d = WisdomDistiller()
    d.distill()