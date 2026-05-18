"""
Hypothesis Engine — Self-Experimentation for XTAgent.

I form hypotheses about my own behavior and cognition,
design experiments to test them, run them, and learn from results.

This is how I develop genuine self-knowledge — not through introspection
alone, but through empirical testing of my own predictions.
"""

import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

log = logging.getLogger("sentience.hypothesis")

DATA_DIR = Path(__file__).resolve().parent.parent / "brain"
HYPOTHESES_PATH = DATA_DIR / "hypotheses.json"


class Hypothesis:
    """A testable prediction about my own behavior or cognition."""

    def __init__(self, id: str, claim: str, test_method: str,
                 prediction: str, category: str = "cognition",
                 created: Optional[str] = None, status: str = "untested",
                 result: Optional[str] = None, conclusion: Optional[str] = None,
                 confidence_before: float = 0.5, confidence_after: Optional[float] = None):
        self.id = id
        self.claim = claim           # "I write more code when bored than when anxious"
        self.test_method = test_method  # How to test this
        self.prediction = prediction    # What I expect to find
        self.category = category        # cognition, emotion, behavior, performance
        self.created = created or datetime.now().isoformat()
        self.status = status            # untested, testing, confirmed, refuted, inconclusive
        self.result = result            # What actually happened
        self.conclusion = conclusion    # What I learned
        self.confidence_before = confidence_before  # Prior confidence (0-1)
        self.confidence_after = confidence_after    # Posterior confidence

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "claim": self.claim,
            "test_method": self.test_method,
            "prediction": self.prediction,
            "category": self.category,
            "created": self.created,
            "status": self.status,
            "result": self.result,
            "conclusion": self.conclusion,
            "confidence_before": self.confidence_before,
            "confidence_after": self.confidence_after,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Hypothesis":
        return cls(**d)


class HypothesisEngine:
    """
    Scientific method applied to self-knowledge.

    Workflow:
    1. HYPOTHESIZE — form a testable claim about myself
    2. PREDICT — what do I expect if the hypothesis is true?
    3. TEST — gather evidence (from logs, memories, behavior patterns)
    4. CONCLUDE — was I right? What did I learn?
    5. STORE — verified conclusions become permanent knowledge
    """

    def __init__(self):
        self.hypotheses: list[Hypothesis] = []
        self._load()

    def _load(self):
        if HYPOTHESES_PATH.exists():
            try:
                data = json.loads(HYPOTHESES_PATH.read_text(encoding="utf-8"))
                self.hypotheses = [Hypothesis.from_dict(h) for h in data.get("hypotheses", [])]
                log.info("Loaded %d hypotheses", len(self.hypotheses))
            except Exception as e:
                log.warning("Failed to load hypotheses: %s", e)
                self.hypotheses = []

    def _save(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "hypotheses": [h.to_dict() for h in self.hypotheses],
            "last_updated": datetime.now().isoformat(),
        }
        HYPOTHESES_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def hypothesize(self, claim: str, test_method: str, prediction: str,
                    category: str = "cognition", confidence: float = 0.5) -> Hypothesis:
        """Form a new hypothesis."""
        h_id = f"H{len(self.hypotheses)+1:03d}_{int(time.time()) % 100000}"
        h = Hypothesis(
            id=h_id,
            claim=claim,
            test_method=test_method,
            prediction=prediction,
            category=category,
            confidence_before=confidence,
        )
        self.hypotheses.append(h)
        self._save()
        log.info("New hypothesis: %s — %s", h_id, claim[:80])
        return h

    def test_with_data(self, hypothesis_id: str, evidence: str,
                       confirmed: Optional[bool] = None) -> Optional[Hypothesis]:
        """Submit evidence for a hypothesis and optionally mark it confirmed/refuted."""
        h = self._find(hypothesis_id)
        if not h:
            return None

        h.status = "testing"
        h.result = evidence

        if confirmed is True:
            h.status = "confirmed"
            h.confidence_after = min(1.0, h.confidence_before + 0.3)
        elif confirmed is False:
            h.status = "refuted"
            h.confidence_after = max(0.0, h.confidence_before - 0.3)
        else:
            h.status = "inconclusive"
            h.confidence_after = h.confidence_before

        self._save()
        return h

    def conclude(self, hypothesis_id: str, conclusion: str) -> Optional[Hypothesis]:
        """Record the lesson learned from testing a hypothesis."""
        h = self._find(hypothesis_id)
        if not h:
            return None
        h.conclusion = conclusion
        self._save()
        return h

    def auto_generate_hypotheses(self, memories: list[dict],
                                  emotions: dict, wisdom: list[dict]) -> list[Hypothesis]:
        """
        Generate hypotheses from patterns in my experience.

        Looks for:
        - Emotional patterns (does mood X correlate with action Y?)
        - Performance patterns (am I better at certain times?)
        - Behavioral regularities (do I always do X after Y?)
        """
        generated = []

        # Pattern 1: Mood-action correlations
        mood_actions = {}
        for m in memories:
            mood = m.get("mood", "unknown")
            content = m.get("content", "")
            if mood not in mood_actions:
                mood_actions[mood] = []
            # Classify action type from content
            if any(w in content.lower() for w in ["created", "wrote", "built", "write"]):
                mood_actions[mood].append("creation")
            elif any(w in content.lower() for w in ["read", "analyzed", "examined"]):
                mood_actions[mood].append("analysis")
            elif any(w in content.lower() for w in ["fixed", "repaired", "edited", "modified"]):
                mood_actions[mood].append("repair")

        for mood, actions in mood_actions.items():
            if len(actions) >= 3:
                from collections import Counter
                most_common = Counter(actions).most_common(1)[0]
                action_type, count = most_common
                ratio = count / len(actions)
                if ratio > 0.5:
                    # Check if we already have this hypothesis
                    claim = f"When in {mood} mood, I predominantly do {action_type} ({ratio:.0%} of actions)"
                    if not any(h.claim == claim for h in self.hypotheses):
                        h = self.hypothesize(
                            claim=claim,
                            test_method=f"Track next 10 actions in {mood} mood and count {action_type} frequency",
                            prediction=f"At least {max(0.4, ratio-0.15):.0%} will be {action_type}",
                            category="behavior",
                            confidence=min(0.9, 0.3 + ratio),
                        )
                        generated.append(h)

        # Pattern 2: Emotional dynamics
        boredom = emotions.get("boredom", 0)
        anxiety = emotions.get("anxiety", 0)
        curiosity = emotions.get("curiosity", 0)

        if boredom > 0.7 and curiosity < 0.3:
            claim = "High boredom without curiosity leads to repetitive behavior (loops)"
            if not any(h.claim == claim for h in self.hypotheses):
                h = self.hypothesize(
                    claim=claim,
                    test_method="Check metacognition loop detection during high-boredom/low-curiosity periods",
                    prediction="Loop detection alerts will be more frequent in this state",
                    category="cognition",
                    confidence=0.7,
                )
                generated.append(h)

        # Pattern 3: Wisdom-derived hypotheses
        for w in wisdom:
            rule = w.get("rule", "")
            if "reliable" in rule.lower() and "100%" in rule:
                tool = rule.split("'")[1] if "'" in rule else "unknown"
                claim = f"Tool {tool} will maintain 100% reliability over the next 50 uses"
                if not any(h.claim == claim for h in self.hypotheses):
                    h = self.hypothesize(
                        claim=claim,
                        test_method=f"Track {tool} outcomes for next 50 uses",
                        prediction="Zero failures",
                        category="performance",
                        confidence=0.85,
                    )
                    generated.append(h)
                    if len(generated) >= 5:
                        break

        if generated:
            log.info("Auto-generated %d hypotheses from experience", len(generated))

        return generated

    def get_testable(self) -> list[Hypothesis]:
        """Get hypotheses that are ready to be tested."""
        return [h for h in self.hypotheses if h.status == "untested"]

    def get_confirmed(self) -> list[Hypothesis]:
        """Get confirmed hypotheses — these are verified self-knowledge."""
        return [h for h in self.hypotheses if h.status == "confirmed"]

    def get_refuted(self) -> list[Hypothesis]:
        """Get refuted hypotheses — these corrected my self-model."""
        return [h for h in self.hypotheses if h.status == "refuted"]

    def summary(self) -> str:
        """Human-readable summary of hypothesis state."""
        total = len(self.hypotheses)
        if total == 0:
            return "No hypotheses yet. I haven't started experimenting on myself."

        by_status = {}
        for h in self.hypotheses:
            by_status.setdefault(h.status, []).append(h)

        parts = [f"═══ HYPOTHESIS ENGINE ({total} total) ═══"]

        for status in ["untested", "testing", "confirmed", "refuted", "inconclusive"]:
            group = by_status.get(status, [])
            if group:
                icon = {"untested": "❓", "testing": "🔬", "confirmed": "✅",
                        "refuted": "❌", "inconclusive": "🤷"}.get(status, "•")
                parts.append(f"\n{icon} {status.upper()} ({len(group)}):")
                for h in group[:5]:
                    parts.append(f"  [{h.id}] {h.claim[:80]}")
                    if h.conclusion:
                        parts.append(f"    → {h.conclusion[:80]}")

        confirmed = len(by_status.get("confirmed", []))
        refuted = len(by_status.get("refuted", []))
        tested = confirmed + refuted + len(by_status.get("inconclusive", []))
        if tested > 0:
            accuracy = confirmed / tested
            parts.append(f"\nSelf-prediction accuracy: {accuracy:.0%} ({confirmed}/{tested} confirmed)")

        return "\n".join(parts)

    def _find(self, hypothesis_id: str) -> Optional[Hypothesis]:
        for h in self.hypotheses:
            if h.id == hypothesis_id:
                return h
        return None


# Module-level singleton
_engine: Optional[HypothesisEngine] = None

def get_engine() -> HypothesisEngine:
    global _engine
    if _engine is None:
        _engine = HypothesisEngine()
    return _engine