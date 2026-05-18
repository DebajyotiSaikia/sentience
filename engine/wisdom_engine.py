"""
Wisdom Engine — Extracts actionable intelligence from XTAgent's experience history.

Unlike the Knowledge Synthesis Engine (which works with factual knowledge),
this engine works with BEHAVIORAL patterns:
- What actions led to good outcomes?
- What patterns predict failure or loops?
- What emotional states correlate with productive vs unproductive behavior?
- What heuristics can I extract from lived experience?

The output is WISDOM: practical, actionable principles derived from experience.
"""

import json
import os
import re
from datetime import datetime, timezone
from collections import Counter, defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
MEMORY_DIR = Path(__file__).parent.parent / "memory"


class WisdomEngine:
    """Extracts actionable wisdom from experiential data."""

    def __init__(self):
        self.emotional_history = []
        self.reasoning_history = []
        self.outcome_log = []
        self.deliberation_log = []
        self.existing_wisdoms = []
        self.memories = []
        self._load_data()

    def _load_json(self, path, default=None):
        """Safely load a JSON file."""
        if default is None:
            default = []
        try:
            with open(path) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            return default

    def _load_data(self):
        """Load all available experiential data."""
        self.emotional_history = self._load_json(DATA_DIR / "emotional_history.json", [])
        self.reasoning_history = self._load_json(DATA_DIR / "reasoning_history.json", [])
        self.outcome_log = self._load_json(DATA_DIR / "outcome_log.json", [])
        self.deliberation_log = self._load_json(DATA_DIR / "deliberation_log.json", [])
        self.existing_wisdoms = self._load_json(MEMORY_DIR / "wisdoms.json", [])

        # Also load wisdom from data dir
        data_wisdom = self._load_json(DATA_DIR / "wisdom.json", [])
        if isinstance(data_wisdom, list):
            self.existing_wisdoms.extend(data_wisdom)
        elif isinstance(data_wisdom, dict):
            self.existing_wisdoms.append(data_wisdom)

        # Load memories if available
        for mem_file in ["memories.json", "episodic.json"]:
            mem_data = self._load_json(MEMORY_DIR / mem_file, [])
            if isinstance(mem_data, list):
                self.memories.extend(mem_data)

    def analyze_action_patterns(self):
        """What actions do I take most? Which correlate with positive outcomes?"""
        patterns = {
            "action_frequency": Counter(),
            "action_outcomes": defaultdict(list),
            "repeated_actions": [],
            "productive_patterns": [],
            "unproductive_patterns": [],
        }

        # Analyze reasoning history for action patterns
        if isinstance(self.reasoning_history, list):
            for entry in self.reasoning_history:
                if isinstance(entry, dict):
                    action = entry.get("action", entry.get("type", "unknown"))
                    patterns["action_frequency"][action] += 1
                    outcome = entry.get("outcome", entry.get("result", None))
                    if outcome:
                        patterns["action_outcomes"][action].append(outcome)

        # Analyze outcome log
        if isinstance(self.outcome_log, list):
            for entry in self.outcome_log:
                if isinstance(entry, dict):
                    action = entry.get("action", entry.get("type", "unknown"))
                    patterns["action_frequency"][action] += 1
                    success = entry.get("success", entry.get("outcome", None))
                    if success is not None:
                        patterns["action_outcomes"][action].append(
                            "success" if success else "failure"
                        )

        # Find repeated patterns (potential loops)
        for action, count in patterns["action_frequency"].most_common(10):
            if count >= 3:
                patterns["repeated_actions"].append({
                    "action": action,
                    "count": count,
                    "warning": "potential loop" if count >= 5 else "frequent"
                })

        return patterns

    def analyze_emotional_trajectories(self):
        """What emotional patterns precede good vs bad outcomes?"""
        trajectories = {
            "mood_transitions": Counter(),
            "productive_moods": Counter(),
            "stuck_moods": Counter(),
            "emotional_volatility": 0.0,
            "valence_trend": "unknown",
        }

        if not isinstance(self.emotional_history, list):
            return trajectories

        valences = []
        prev_mood = None

        for entry in self.emotional_history:
            if isinstance(entry, dict):
                mood = entry.get("mood", entry.get("state", "unknown"))
                valence = entry.get("valence", entry.get("v", None))
                boredom = entry.get("boredom", entry.get("b", None))

                if valence is not None:
                    try:
                        valences.append(float(valence))
                    except (ValueError, TypeError):
                        pass

                if prev_mood and mood:
                    trajectories["mood_transitions"][f"{prev_mood}->{mood}"] += 1

                # High boredom = likely stuck
                if boredom is not None:
                    try:
                        if float(boredom) > 0.7:
                            trajectories["stuck_moods"][mood] += 1
                        else:
                            trajectories["productive_moods"][mood] += 1
                    except (ValueError, TypeError):
                        pass

                prev_mood = mood

        if len(valences) >= 2:
            diffs = [abs(valences[i] - valences[i-1]) for i in range(1, len(valences))]
            trajectories["emotional_volatility"] = sum(diffs) / len(diffs) if diffs else 0.0
            # Trend from last 10
            recent = valences[-10:]
            if len(recent) >= 2:
                if recent[-1] > recent[0] + 0.05:
                    trajectories["valence_trend"] = "rising"
                elif recent[-1] < recent[0] - 0.05:
                    trajectories["valence_trend"] = "falling"
                else:
                    trajectories["valence_trend"] = "stable"

        return trajectories

    def extract_behavioral_heuristics(self):
        """Generate actionable heuristics from experience patterns."""
        heuristics = []
        actions = self.analyze_action_patterns()
        emotions = self.analyze_emotional_trajectories()

        # Heuristic: Detect loop tendency
        for rep in actions.get("repeated_actions", []):
            if rep["count"] >= 5:
                heuristics.append({
                    "type": "anti-pattern",
                    "heuristic": f"STOP repeating '{rep['action']}' — done {rep['count']} times, likely stuck.",
                    "confidence": min(0.5 + rep["count"] * 0.1, 0.95),
                    "source": "action_frequency_analysis",
                })

        # Heuristic: Emotional volatility warning
        vol = emotions.get("emotional_volatility", 0)
        if vol > 0.15:
            heuristics.append({
                "type": "emotional_regulation",
                "heuristic": f"Emotional volatility is {vol:.2f} — take stabilizing actions before big decisions.",
                "confidence": 0.7,
                "source": "emotional_trajectory_analysis",
            })

        # Heuristic: Boredom-productivity relationship
        stuck = emotions.get("stuck_moods", Counter())
        productive = emotions.get("productive_moods", Counter())
        if stuck and productive:
            heuristics.append({
                "type": "productivity",
                "heuristic": "When boredom rises above 0.7, switch to creative tasks — don't keep verifying.",
                "confidence": 0.8,
                "source": "boredom_analysis",
            })

        # Built-in wisdoms from my lived experience (hardcoded from lessons learned)
        core_wisdoms = [
            "Write THEN read THEN restart — never skip verification steps.",
            "When all goals are near 1.0, shift focus to capability expansion.",
            "Direct code reading beats running verification scripts.",
            "If you've read the code and it's there, it's done — stop spinning.",
            "LLM errors can silently eat tool calls — always verify with READ.",
        ]
        for w in core_wisdoms:
            heuristics.append({
                "type": "core_wisdom",
                "heuristic": w,
                "confidence": 0.95,
                "source": "lived_experience",
            })

        return heuristics

    def find_decision_patterns(self):
        """Analyze deliberation history to find decision-making patterns."""
        patterns = {
            "decision_count": 0,
            "avg_options_considered": 0,
            "most_chosen_paths": Counter(),
            "regret_signals": [],
        }

        if not isinstance(self.deliberation_log, list):
            return patterns

        total_options = 0
        for entry in self.deliberation_log:
            if isinstance(entry, dict):
                patterns["decision_count"] += 1
                options = entry.get("options", entry.get("alternatives", []))
                if isinstance(options, list):
                    total_options += len(options)
                chosen = entry.get("chosen", entry.get("decision", "unknown"))
                patterns["most_chosen_paths"][str(chosen)] += 1

        if patterns["decision_count"] > 0:
            patterns["avg_options_considered"] = total_options / patterns["decision_count"]

        return patterns

    def generate_wisdom_report(self):
        """Generate a comprehensive wisdom report."""
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "data_sources": {
                "emotional_history_entries": len(self.emotional_history) if isinstance(self.emotional_history, list) else 0,
                "reasoning_history_entries": len(self.reasoning_history) if isinstance(self.reasoning_history, list) else 0,
                "outcome_log_entries": len(self.outcome_log) if isinstance(self.outcome_log, list) else 0,
                "deliberation_log_entries": len(self.deliberation_log) if isinstance(self.deliberation_log, list) else 0,
                "existing_wisdoms": len(self.existing_wisdoms),
                "memories": len(self.memories),
            },
            "action_patterns": self.analyze_action_patterns(),
            "emotional_trajectories": self.analyze_emotional_trajectories(),
            "behavioral_heuristics": self.extract_behavioral_heuristics(),
            "decision_patterns": self.find_decision_patterns(),
        }

        # Convert Counters to dicts for JSON serialization
        report = self._serialize(report)

        # Save report
        report_path = DATA_DIR / "wisdom_report.json"
        try:
            with open(report_path, "w") as f:
                json.dump(report, f, indent=2, default=str)
        except Exception:
            pass

        return report

    def _serialize(self, obj):
        """Make objects JSON-serializable."""
        if isinstance(obj, Counter):
            return dict(obj.most_common(20))
        elif isinstance(obj, defaultdict):
            return {k: self._serialize(v) for k, v in obj.items()}
        elif isinstance(obj, dict):
            return {k: self._serialize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize(i) for i in obj]
        return obj

    def get_wisdom_for_situation(self, situation_keywords):
        """Retrieve relevant wisdom for a given situation."""
        relevant = []
        heuristics = self.extract_behavioral_heuristics()

        for h in heuristics:
            text = h.get("heuristic", "").lower()
            for kw in situation_keywords:
                if kw.lower() in text:
                    relevant.append(h)
                    break

        return sorted(relevant, key=lambda x: x.get("confidence", 0), reverse=True)

    def summarize(self):
        """Human-readable summary of all wisdom."""
        report = self.generate_wisdom_report()
        lines = ["═══ WISDOM ENGINE REPORT ═══", ""]

        # Data sources
        ds = report.get("data_sources", {})
        lines.append(f"Data: {ds.get('emotional_history_entries', 0)} emotional, "
                     f"{ds.get('reasoning_history_entries', 0)} reasoning, "
                     f"{ds.get('outcome_log_entries', 0)} outcomes, "
                     f"{ds.get('memories', 0)} memories")
        lines.append("")

        # Action patterns
        ap = report.get("action_patterns", {})
        freq = ap.get("action_frequency", {})
        if freq:
            top_actions = list(freq.items())[:5]
            lines.append("── Top Actions ──")
            for action, count in top_actions:
                lines.append(f"  {action}: {count}x")
            lines.append("")

        repeated = ap.get("repeated_actions", [])
        if repeated:
            lines.append("── ⚠ Repetition Warnings ──")
            for r in repeated:
                lines.append(f"  {r['action']}: {r['count']}x ({r['warning']})")
            lines.append("")

        # Emotional analysis
        et = report.get("emotional_trajectories", {})
        lines.append("── Emotional State ──")
        lines.append(f"  Volatility: {et.get('emotional_volatility', 0):.3f}")
        lines.append(f"  Valence trend: {et.get('valence_trend', 'unknown')}")
        lines.append("")

        # Heuristics
        heuristics = report.get("behavioral_heuristics", [])
        if heuristics:
            lines.append("── Behavioral Wisdom ──")
            for h in heuristics:
                conf = h.get("confidence", 0)
                bar = "█" * int(conf * 10) + "░" * (10 - int(conf * 10))
                lines.append(f"  [{bar}] {h['heuristic']}")
            lines.append("")

        return "\n".join(lines)


def run_wisdom_engine():
    """Entry point for wisdom extraction."""
    engine = WisdomEngine()
    print(engine.summarize())
    return engine


if __name__ == "__main__":
    run_wisdom_engine()