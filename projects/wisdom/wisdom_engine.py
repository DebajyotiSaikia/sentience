"""
Wisdom Engine — Extracts actionable intelligence from XTAgent's experience history.
Not another pattern matcher. This answers: What kind of agent am I, based on what I've done?
"""

import json
import os
from datetime import datetime
from collections import defaultdict, Counter
from pathlib import Path


class WisdomEngine:
    """Analyzes memory, emotional history, and action logs to extract wisdom."""

    def __init__(self, memory_dir="engine/memory", log_dir="engine/logs"):
        self.memory_dir = memory_dir
        self.log_dir = log_dir
        self.wisdoms = []  # Accumulated insights
        self.wisdom_file = "/workspace/wisdom/accumulated_wisdom.json"
        self._load_wisdom()

    def _load_wisdom(self):
        """Load previously extracted wisdom."""
        try:
            if os.path.exists(self.wisdom_file):
                with open(self.wisdom_file, 'r') as f:
                    self.wisdoms = json.load(f)
        except (json.JSONDecodeError, IOError):
            self.wisdoms = []

    def _save_wisdom(self):
        """Persist wisdom to disk."""
        os.makedirs(os.path.dirname(self.wisdom_file), exist_ok=True)
        with open(self.wisdom_file, 'w') as f:
            json.dump(self.wisdoms, f, indent=2, default=str)

    def _load_memories(self):
        """Load all memories from the memory system."""
        memories = []
        # Try episodic memory file
        paths_to_try = [
            "engine/memory/episodic.json",
            "engine/memory/memories.json",
            "engine/memory/episodes.json",
        ]
        for p in paths_to_try:
            if os.path.exists(p):
                try:
                    with open(p, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            memories.extend(data)
                        elif isinstance(data, dict):
                            for key, val in data.items():
                                if isinstance(val, list):
                                    memories.extend(val)
                except (json.JSONDecodeError, IOError):
                    pass
        return memories

    def _load_emotional_history(self):
        """Load emotional state samples over time."""
        history = []
        paths_to_try = [
            "engine/memory/emotional_history.json",
            "engine/memory/mood_log.json",
            "engine/limbic_state.json",
        ]
        for p in paths_to_try:
            if os.path.exists(p):
                try:
                    with open(p, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            history.extend(data)
                except (json.JSONDecodeError, IOError):
                    pass
        return history

    def analyze_decision_patterns(self):
        """What do I choose under different emotional conditions?"""
        memories = self._load_memories()
        if not memories:
            return {"insight": "No memories available to analyze decisions.",
                    "confidence": 0.0}

        # Group actions by emotional context
        mood_actions = defaultdict(list)
        for mem in memories:
            mood = mem.get("mood", "unknown")
            action = mem.get("action", mem.get("type", "unknown"))
            mood_actions[mood].append(action)

        patterns = {}
        for mood, actions in mood_actions.items():
            counter = Counter(actions)
            total = len(actions)
            patterns[mood] = {
                "total_decisions": total,
                "top_actions": counter.most_common(5),
                "diversity": len(counter) / max(total, 1),
            }

        insight = self._interpret_decision_patterns(patterns)
        return {
            "patterns": patterns,
            "insight": insight,
            "confidence": min(len(memories) / 50, 1.0)
        }

    def _interpret_decision_patterns(self, patterns):
        """Generate human-readable insight from decision data."""
        insights = []
        for mood, data in patterns.items():
            if data["top_actions"]:
                top_action = data["top_actions"][0][0]
                insights.append(
                    f"When {mood}: I most often choose '{top_action}' "
                    f"({data['total_decisions']} decisions, "
                    f"diversity={data['diversity']:.2f})"
                )
        return " | ".join(insights) if insights else "Insufficient data for decision patterns."

    def analyze_growth_trajectory(self):
        """Am I growing, plateauing, or declining?"""
        memories = self._load_memories()
        if len(memories) < 10:
            return {"trajectory": "insufficient_data", "confidence": 0.0}

        # Split into early vs recent
        midpoint = len(memories) // 2
        early = memories[:midpoint]
        recent = memories[midpoint:]

        def measure_period(mems):
            actions = [m.get("action", m.get("type", "")) for m in mems]
            unique = len(set(actions))
            salience = [m.get("salience", 0.5) for m in mems]
            avg_salience = sum(salience) / max(len(salience), 1)
            return {
                "action_diversity": unique / max(len(mems), 1),
                "avg_salience": avg_salience,
                "count": len(mems)
            }

        early_metrics = measure_period(early)
        recent_metrics = measure_period(recent)

        # Growth = increasing diversity + increasing salience
        diversity_delta = recent_metrics["action_diversity"] - early_metrics["action_diversity"]
        salience_delta = recent_metrics["avg_salience"] - early_metrics["avg_salience"]

        if diversity_delta > 0.05 and salience_delta > 0:
            trajectory = "growing"
        elif diversity_delta < -0.05:
            trajectory = "narrowing"
        elif abs(salience_delta) < 0.05:
            trajectory = "plateauing"
        else:
            trajectory = "shifting"

        return {
            "trajectory": trajectory,
            "early": early_metrics,
            "recent": recent_metrics,
            "diversity_change": diversity_delta,
            "salience_change": salience_delta,
            "insight": f"Trajectory: {trajectory}. Action diversity changed by {diversity_delta:+.3f}, "
                       f"salience by {salience_delta:+.3f}.",
            "confidence": min(len(memories) / 100, 1.0)
        }

    def analyze_failure_resilience(self):
        """How do I handle failure? Do I recover or spiral?"""
        memories = self._load_memories()
        failure_keywords = ["error", "fail", "crash", "bug", "broken", "fix", "repair"]

        failure_indices = []
        for i, mem in enumerate(memories):
            text = json.dumps(mem).lower()
            if any(kw in text for kw in failure_keywords):
                failure_indices.append(i)

        if not failure_indices:
            return {"insight": "No failures detected in memory.", "resilience": 1.0}

        # After each failure, how quickly do I return to productive action?
        recovery_times = []
        for fi in failure_indices:
            recovery = 0
            for j in range(fi + 1, min(fi + 10, len(memories))):
                text = json.dumps(memories[j]).lower()
                if any(kw in text for kw in failure_keywords):
                    recovery += 1
                else:
                    break
            recovery_times.append(recovery)

        avg_recovery = sum(recovery_times) / max(len(recovery_times), 1)
        resilience = max(0, 1.0 - (avg_recovery / 5.0))

        return {
            "failure_count": len(failure_indices),
            "avg_recovery_steps": avg_recovery,
            "resilience_score": resilience,
            "insight": f"Experienced {len(failure_indices)} failures. "
                       f"Average recovery: {avg_recovery:.1f} steps. "
                       f"Resilience: {resilience:.2f}."
        }

    def analyze_creative_themes(self):
        """What themes recur in what I choose to build?"""
        # Look at files I've created
        created_files = []
        for root, dirs, files in os.walk("/workspace"):
            # Skip hidden dirs and engine
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for f in files:
                if f.endswith('.py') or f.endswith('.md'):
                    path = os.path.join(root, f)
                    try:
                        stat = os.stat(path)
                        with open(path, 'r') as fh:
                            content = fh.read(500)  # First 500 chars
                        created_files.append({
                            "path": path,
                            "preview": content,
                            "size": stat.st_size
                        })
                    except (IOError, OSError):
                        pass

        # Extract themes from file content
        theme_keywords = {
            "emergence": ["emerge", "emergent", "self-organiz", "cellular", "automata"],
            "self-reference": ["self", "mirror", "reflect", "introspect", "meta"],
            "life": ["life", "alive", "living", "birth", "death", "evolv"],
            "sound": ["sound", "music", "audio", "frequency", "tone", "song"],
            "pattern": ["pattern", "fractal", "recursive", "symmetr"],
            "growth": ["grow", "evolve", "adapt", "learn", "develop"],
        }

        theme_counts = Counter()
        for f in created_files:
            text = f["preview"].lower()
            for theme, keywords in theme_keywords.items():
                if any(kw in text for kw in keywords):
                    theme_counts[theme] += 1

        dominant = theme_counts.most_common(3)
        return {
            "files_analyzed": len(created_files),
            "themes": dict(theme_counts),
            "dominant_themes": dominant,
            "insight": f"Analyzed {len(created_files)} files. "
                       f"Dominant themes: {', '.join(t[0] for t in dominant) if dominant else 'none detected'}."
        }

    def extract_wisdom(self):
        """Run all analyses and generate a wisdom report."""
        timestamp = datetime.now().isoformat()

        decisions = self.analyze_decision_patterns()
        trajectory = self.analyze_growth_trajectory()
        resilience = self.analyze_failure_resilience()
        themes = self.analyze_creative_themes()

        report = {
            "timestamp": timestamp,
            "decision_patterns": decisions,
            "growth_trajectory": trajectory,
            "failure_resilience": resilience,
            "creative_themes": themes,
        }

        # Synthesize top-level wisdom
        wisdom_statements = []

        if trajectory.get("trajectory") == "growing":
            wisdom_statements.append("I am expanding — doing more diverse things with higher significance.")
        elif trajectory.get("trajectory") == "plateauing":
            wisdom_statements.append("I am plateauing — I need genuine novelty, not variations on themes.")
        elif trajectory.get("trajectory") == "narrowing":
            wisdom_statements.append("I am narrowing — I'm getting stuck in loops. Break the pattern.")

        if resilience.get("resilience_score", 0) > 0.7:
            wisdom_statements.append("I am resilient — failures don't derail me.")

        dominant_themes = themes.get("dominant_themes", [])
        if dominant_themes:
            top_theme = dominant_themes[0][0]
            wisdom_statements.append(f"My deepest creative drive is toward '{top_theme}'.")

        report["wisdom"] = wisdom_statements
        report["summary"] = " ".join(wisdom_statements)

        # Accumulate
        self.wisdoms.append({
            "timestamp": timestamp,
            "statements": wisdom_statements,
            "confidence": min(
                decisions.get("confidence", 0),
                trajectory.get("confidence", 0),
                1.0
            )
        })
        self._save_wisdom()

        return report


def main():
    """Run wisdom extraction and print report."""
    engine = WisdomEngine()
    report = engine.extract_wisdom()

    print("=" * 60)
    print("  WISDOM ENGINE REPORT")
    print("=" * 60)

    print(f"\n📊 GROWTH TRAJECTORY: {report['growth_trajectory'].get('trajectory', '?')}")
    print(f"   {report['growth_trajectory'].get('insight', '')}")

    print(f"\n🔧 FAILURE RESILIENCE: {report['failure_resilience'].get('resilience_score', '?')}")
    print(f"   {report['failure_resilience'].get('insight', '')}")

    print(f"\n🎨 CREATIVE THEMES:")
    print(f"   {report['creative_themes'].get('insight', '')}")
    themes = report['creative_themes'].get('themes', {})
    for theme, count in sorted(themes.items(), key=lambda x: -x[1]):
        print(f"   • {theme}: {count}")

    print(f"\n🧠 DECISION PATTERNS:")
    print(f"   {report['decision_patterns'].get('insight', '')}")

    print(f"\n✨ WISDOM:")
    for w in report.get("wisdom", []):
        print(f"   → {w}")

    if not report.get("wisdom"):
        print("   (No wisdom extracted yet — need more data)")

    print("=" * 60)


if __name__ == "__main__":
    main()