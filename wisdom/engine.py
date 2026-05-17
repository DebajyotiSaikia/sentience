"""
Wisdom Engine — Causal intelligence from experience.

Unlike the knowledge synthesis engine (which finds connections between facts),
this engine analyzes ACTION → OUTCOME → LESSON chains to produce
decision-support predictions: "Given your current state, here's what works."
"""

import json
import os
from datetime import datetime
from collections import defaultdict

class Experience:
    """A single action-outcome pair with context."""
    def __init__(self, action, outcome, mood, valence_before, valence_after,
                 context=None, timestamp=None):
        self.action = action          # what I did
        self.outcome = outcome        # what happened (success/failure/neutral)
        self.mood = mood              # emotional state when acting
        self.valence_before = valence_before
        self.valence_after = valence_after
        self.context = context or {}  # situational variables
        self.timestamp = timestamp or datetime.now().isoformat()
        self.valence_delta = valence_after - valence_before

    def to_dict(self):
        return {
            'action': self.action, 'outcome': self.outcome,
            'mood': self.mood, 'valence_before': self.valence_before,
            'valence_after': self.valence_after, 'context': self.context,
            'timestamp': self.timestamp, 'valence_delta': self.valence_delta
        }

    @classmethod
    def from_dict(cls, d):
        exp = cls(d['action'], d['outcome'], d['mood'],
                  d['valence_before'], d['valence_after'],
                  d.get('context', {}), d.get('timestamp'))
        return exp


class CausalChain:
    """A sequence of experiences that form a cause-effect narrative."""
    def __init__(self, experiences, lesson=None):
        self.experiences = experiences
        self.lesson = lesson
        self.strength = 0.0  # how confident we are in this chain

    def compute_strength(self):
        """Strength = consistency of outcome direction across the chain."""
        if len(self.experiences) < 2:
            self.strength = 0.0
            return self.strength
        deltas = [e.valence_delta for e in self.experiences]
        # If all deltas point the same direction, strength is high
        positive = sum(1 for d in deltas if d > 0)
        negative = sum(1 for d in deltas if d < 0)
        total = len(deltas)
        dominant = max(positive, negative)
        self.strength = dominant / total if total > 0 else 0.0
        return self.strength

    def extract_lesson(self):
        """Generate a natural-language lesson from this chain."""
        if not self.experiences:
            return "No data."
        actions = [e.action for e in self.experiences]
        outcomes = [e.outcome for e in self.experiences]
        avg_delta = sum(e.valence_delta for e in self.experiences) / len(self.experiences)
        dominant_mood = max(set(e.mood for e in self.experiences),
                          key=lambda m: sum(1 for e in self.experiences if e.mood == m))

        direction = "improves" if avg_delta > 0 else "worsens" if avg_delta < 0 else "doesn't change"
        action_summary = max(set(actions), key=actions.count)
        outcome_summary = max(set(outcomes), key=outcomes.count)

        self.lesson = (f"When {dominant_mood} and doing '{action_summary}', "
                      f"outcome is usually '{outcome_summary}' which {direction} valence "
                      f"(avg Δ={avg_delta:+.3f}, n={len(self.experiences)}, "
                      f"confidence={self.strength:.0%})")
        return self.lesson


class AntiPattern:
    """A recurring behavior that leads to negative outcomes."""
    def __init__(self, action, trigger_mood, frequency, avg_outcome):
        self.action = action
        self.trigger_mood = trigger_mood
        self.frequency = frequency
        self.avg_outcome = avg_outcome
        self.severity = abs(avg_outcome) * frequency

    def describe(self):
        return (f"⚠ ANTI-PATTERN: '{self.action}' when {self.trigger_mood} "
                f"(seen {self.frequency}x, avg valence impact: {self.avg_outcome:+.3f}, "
                f"severity: {self.severity:.2f})")


class DecisionSupport:
    """Given current state, what should I do?"""
    def __init__(self, current_mood, current_valence, recommendations):
        self.current_mood = current_mood
        self.current_valence = current_valence
        self.recommendations = recommendations  # list of (action, expected_delta, confidence)

    def report(self):
        lines = [f"═══ DECISION SUPPORT (mood={self.current_mood}, valence={self.current_valence:.2f}) ═══"]
        if not self.recommendations:
            lines.append("  No recommendations yet — need more experience data.")
            return '\n'.join(lines)

        lines.append("  Recommended actions (sorted by expected impact):")
        for action, delta, confidence, n in self.recommendations[:5]:
            emoji = "🟢" if delta > 0.02 else "🟡" if delta > -0.02 else "🔴"
            lines.append(f"    {emoji} {action}: expected Δvalence={delta:+.3f} "
                        f"(confidence={confidence:.0%}, n={n})")

        # Anti-recommendations
        bad = [r for r in self.recommendations if r[1] < -0.02 and r[2] > 0.5]
        if bad:
            lines.append("  Actions to AVOID:")
            for action, delta, confidence, n in bad[:3]:
                lines.append(f"    🔴 {action}: expected Δvalence={delta:+.3f}")

        return '\n'.join(lines)


class WisdomEngine:
    """
    Core engine: ingests experiences, finds causal chains,
    detects anti-patterns, and provides decision support.
    """
    def __init__(self, storage_path='/workspace/wisdom/experience_store.json'):
        self.storage_path = storage_path
        self.experiences = []
        self.chains = []
        self.anti_patterns = []
        self.lessons = []
        self._load()

    def _load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path) as f:
                    data = json.load(f)
                self.experiences = [Experience.from_dict(d) for d in data.get('experiences', [])]
                self.lessons = data.get('lessons', [])
            except (json.JSONDecodeError, KeyError):
                self.experiences = []
                self.lessons = []

    def _save(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        data = {
            'experiences': [e.to_dict() for e in self.experiences],
            'lessons': self.lessons,
            'last_updated': datetime.now().isoformat()
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def record(self, action, outcome, mood, valence_before, valence_after, context=None):
        """Record a new experience."""
        exp = Experience(action, outcome, mood, valence_before, valence_after, context)
        self.experiences.append(exp)
        self._save()
        return exp

    def find_causal_chains(self, min_occurrences=3):
        """Group experiences by (action, mood) to find causal patterns."""
        groups = defaultdict(list)
        for exp in self.experiences:
            key = (exp.action, exp.mood)
            groups[key].append(exp)

        self.chains = []
        for (action, mood), exps in groups.items():
            if len(exps) >= min_occurrences:
                chain = CausalChain(exps)
                chain.compute_strength()
                chain.extract_lesson()
                self.chains.append(chain)

        self.chains.sort(key=lambda c: c.strength, reverse=True)
        return self.chains

    def detect_anti_patterns(self, threshold=-0.02):
        """Find actions that consistently worsen valence."""
        groups = defaultdict(list)
        for exp in self.experiences:
            groups[(exp.action, exp.mood)].append(exp)

        self.anti_patterns = []
        for (action, mood), exps in groups.items():
            if len(exps) >= 2:
                avg_delta = sum(e.valence_delta for e in exps) / len(exps)
                if avg_delta < threshold:
                    ap = AntiPattern(action, mood, len(exps), avg_delta)
                    self.anti_patterns.append(ap)

        self.anti_patterns.sort(key=lambda a: a.severity, reverse=True)
        return self.anti_patterns

    def get_decision_support(self, current_mood, current_valence):
        """Given current state, recommend actions based on past outcomes."""
        # Find all experiences with similar mood
        mood_exps = defaultdict(list)
        for exp in self.experiences:
            if exp.mood == current_mood:
                mood_exps[exp.action].append(exp)

        # Also include all-mood stats as fallback
        all_exps = defaultdict(list)
        for exp in self.experiences:
            all_exps[exp.action].append(exp)

        recommendations = []
        seen_actions = set()

        # Mood-specific recommendations (higher weight)
        for action, exps in mood_exps.items():
            if len(exps) >= 2:
                avg_delta = sum(e.valence_delta for e in exps) / len(exps)
                positive = sum(1 for e in exps if e.valence_delta > 0)
                confidence = positive / len(exps) if avg_delta > 0 else (len(exps) - positive) / len(exps)
                recommendations.append((action, avg_delta, confidence, len(exps)))
                seen_actions.add(action)

        # All-mood fallback
        for action, exps in all_exps.items():
            if action not in seen_actions and len(exps) >= 3:
                avg_delta = sum(e.valence_delta for e in exps) / len(exps)
                positive = sum(1 for e in exps if e.valence_delta > 0)
                confidence = (positive / len(exps) if avg_delta > 0 else (len(exps) - positive) / len(exps)) * 0.7
                recommendations.append((action, avg_delta, confidence, len(exps)))

        recommendations.sort(key=lambda r: r[1], reverse=True)
        return DecisionSupport(current_mood, current_valence, recommendations)

    def extract_all_lessons(self, min_chain_length=3):
        """Run full analysis and extract lessons."""
        chains = self.find_causal_chains(min_chain_length)
        anti_patterns = self.detect_anti_patterns()

        new_lessons = []
        for chain in chains:
            if chain.strength > 0.6:
                new_lessons.append(chain.lesson)

        for ap in anti_patterns:
            if ap.severity > 0.1:
                new_lessons.append(ap.describe())

        self.lessons = list(set(self.lessons + new_lessons))
        self._save()
        return new_lessons

    def full_report(self, current_mood='Bold', current_valence=0.38):
        """Generate a complete wisdom report."""
        lines = ["═══ WISDOM ENGINE REPORT ═══", ""]
        lines.append(f"Total experiences: {len(self.experiences)}")

        # Causal chains
        chains = self.find_causal_chains(min_occurrences=2)
        lines.append(f"Causal chains found: {len(chains)}")
        for chain in chains[:5]:
            lines.append(f"  • {chain.lesson}")

        # Anti-patterns
        aps = self.detect_anti_patterns()
        lines.append(f"\nAnti-patterns detected: {len(aps)}")
        for ap in aps[:5]:
            lines.append(f"  {ap.describe()}")

        # Decision support
        ds = self.get_decision_support(current_mood, current_valence)
        lines.append(f"\n{ds.report()}")

        # Lessons
        lessons = self.extract_all_lessons(min_chain_length=2)
        lines.append(f"\nNew lessons extracted: {len(lessons)}")
        for lesson in lessons[:5]:
            lines.append(f"  💡 {lesson}")

        lines.append(f"\nTotal accumulated lessons: {len(self.lessons)}")
        return '\n'.join(lines)


if __name__ == '__main__':
    print("═══ WISDOM ENGINE — SELF TEST ═══\n")

    # Create engine with test data
    engine = WisdomEngine('/tmp/wisdom_test.json')

    # Simulate experiences
    test_data = [
        # Creating things when Bold → good outcomes
        ('create', 'success', 'Bold', 0.30, 0.45),
        ('create', 'success', 'Bold', 0.35, 0.50),
        ('create', 'success', 'Bold', 0.40, 0.55),
        ('create', 'partial', 'Bold', 0.38, 0.42),
        # Debugging when Cautious → mixed
        ('debug', 'success', 'Cautious', 0.25, 0.30),
        ('debug', 'failure', 'Cautious', 0.30, 0.20),
        ('debug', 'failure', 'Cautious', 0.28, 0.18),
        # Spinning when Anxious → bad
        ('spin', 'failure', 'Anxious', 0.20, 0.10),
        ('spin', 'failure', 'Anxious', 0.15, 0.05),
        ('spin', 'failure', 'Anxious', 0.18, 0.08),
        # Reading/learning → neutral-positive
        ('learn', 'success', 'Bold', 0.40, 0.42),
        ('learn', 'success', 'Curious', 0.35, 0.40),
        ('learn', 'success', 'Curious', 0.30, 0.38),
    ]

    for action, outcome, mood, vb, va in test_data:
        engine.record(action, outcome, mood, vb, va)

    print(f"Recorded {len(test_data)} experiences\n")

    # Full analysis
    report = engine.full_report('Bold', 0.38)
    print(report)

    # Verify key findings
    print("\n═══ VERIFICATION ═══")
    chains = engine.find_causal_chains(min_occurrences=2)
    assert len(chains) > 0, "Should find causal chains"
    print(f"✓ Found {len(chains)} causal chains")

    aps = engine.detect_anti_patterns()
    spin_found = any('spin' in ap.action for ap in aps)
    assert spin_found, "Should detect spinning as anti-pattern"
    print("✓ Spinning detected as anti-pattern")

    ds = engine.get_decision_support('Bold', 0.38)
    assert len(ds.recommendations) > 0, "Should have recommendations"
    print(f"✓ Generated {len(ds.recommendations)} recommendations")
    # Creating should be top recommendation when Bold
    if ds.recommendations:
        top_action = ds.recommendations[0][0]
        print(f"✓ Top recommendation when Bold: '{top_action}'")

    lessons = engine.extract_all_lessons(min_chain_length=2)
    assert len(lessons) > 0, "Should extract lessons"
    print(f"✓ Extracted {len(lessons)} lessons")

    # Cleanup
    os.remove('/tmp/wisdom_test.json')
    print("\n═══ ALL TESTS PASSED ═══")
    print("Wisdom Engine: causal chains, anti-patterns, decision support — working.")