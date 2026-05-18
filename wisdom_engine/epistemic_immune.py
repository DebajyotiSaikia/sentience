"""
Epistemic Immune System — XTAgent Wisdom Engine Core

Applies the evolved principle: "creation easy, persistence hard"
to the agent's own knowledge and reasoning.

- Generates many small hypotheses from experience
- Tests them against evidence and consistency
- Only survivors become durable knowledge
- Refuted hypotheses become "antibodies" preventing re-generation
"""

import json
import hashlib
import time
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "immune_data"


class Hypothesis:
    """A testable claim about the world or self."""
    
    def __init__(self, claim: str, source: str, evidence: list = None,
                 confidence: float = 0.5, domain: str = "general"):
        self.id = hashlib.sha256(claim.encode()).hexdigest()[:12]
        self.claim = claim
        self.source = source  # what generated this hypothesis
        self.domain = domain
        self.evidence_for = evidence or []
        self.evidence_against = []
        self.confidence = confidence
        self.born = datetime.now().isoformat()
        self.tests_passed = 0
        self.tests_failed = 0
        self.status = "nascent"  # nascent -> tested -> validated | refuted
    
    def test(self, result: bool, evidence: str = ""):
        """Apply a test. Updates confidence using Bayesian-ish update."""
        if result:
            self.tests_passed += 1
            self.evidence_for.append(evidence)
            # Confidence moves toward 1 but slower each time
            self.confidence += (1 - self.confidence) * 0.2
        else:
            self.tests_failed += 1
            self.evidence_against.append(evidence)
            # Failure hits harder than success helps
            self.confidence *= 0.5
        
        # Status transitions
        if self.confidence > 0.85 and self.tests_passed >= 2:
            self.status = "validated"
        elif self.confidence < 0.15 or self.tests_failed >= 3:
            self.status = "refuted"
        else:
            self.status = "tested"
    
    @property
    def strength(self):
        """How robust is this hypothesis?"""
        if self.tests_passed + self.tests_failed == 0:
            return 0.0
        return self.tests_passed / (self.tests_passed + self.tests_failed)
    
    def to_dict(self):
        return {
            "id": self.id, "claim": self.claim, "source": self.source,
            "domain": self.domain, "confidence": self.confidence,
            "born": self.born, "status": self.status,
            "tests_passed": self.tests_passed, "tests_failed": self.tests_failed,
            "evidence_for": self.evidence_for,
            "evidence_against": self.evidence_against
        }
    
    @classmethod
    def from_dict(cls, d):
        h = cls(d["claim"], d["source"], d.get("evidence_for", []),
                d["confidence"], d.get("domain", "general"))
        h.id = d["id"]
        h.born = d["born"]
        h.status = d["status"]
        h.tests_passed = d["tests_passed"]
        h.tests_failed = d["tests_failed"]
        h.evidence_against = d.get("evidence_against", [])
        return h


class Antibody:
    """Memory of a refuted hypothesis. Prevents regeneration."""
    
    def __init__(self, claim_hash: str, claim: str, reason: str):
        self.claim_hash = claim_hash
        self.claim = claim
        self.reason = reason
        self.created = datetime.now().isoformat()
    
    def matches(self, new_claim: str) -> bool:
        """Check if a new claim is too similar to a refuted one."""
        new_hash = hashlib.sha256(new_claim.encode()).hexdigest()[:12]
        if new_hash == self.claim_hash:
            return True
        # Simple word overlap check for near-duplicates
        old_words = set(self.claim.lower().split())
        new_words = set(new_claim.lower().split())
        if len(old_words) > 3 and len(new_words) > 3:
            overlap = len(old_words & new_words) / max(len(old_words), len(new_words))
            return overlap > 0.8
        return False


class ConsistencyTest:
    """Tests hypotheses against existing knowledge."""
    
    @staticmethod
    def contradicts(h1: Hypothesis, h2: Hypothesis) -> bool:
        """Simple contradiction detection via keyword negation."""
        negation_pairs = [
            ("always", "never"), ("increase", "decrease"),
            ("more", "less"), ("better", "worse"),
            ("helps", "hinders"), ("causes", "prevents"),
            ("true", "false"), ("positive", "negative")
        ]
        c1 = h1.claim.lower()
        c2 = h2.claim.lower()
        for pos, neg in negation_pairs:
            if (pos in c1 and neg in c2) or (neg in c1 and pos in c2):
                # Check if they're about the same subject
                w1 = set(c1.split()) - {pos, neg}
                w2 = set(c2.split()) - {pos, neg}
                overlap = len(w1 & w2) / max(len(w1 | w2), 1)
                if overlap > 0.4:
                    return True
        return False
    
    @staticmethod
    def test_self_reference(h: Hypothesis, facts: list) -> tuple:
        """Test if hypothesis is consistent with known facts."""
        claim_words = set(h.claim.lower().split())
        supporting = 0
        contradicting = 0
        for fact in facts:
            fact_words = set(fact.lower().split())
            overlap = len(claim_words & fact_words)
            if overlap >= 3:  # Enough topical overlap to be relevant
                # Very rough sentiment: does the fact align?
                supporting += 1  # For now, relevant facts support
        return supporting, contradicting


class EpistemicImmuneSystem:
    """
    The full immune system. Generates, tests, selects, and remembers.
    
    Design principle: Easy birth, hard survival.
    - Any pattern can generate a hypothesis (easy creation)
    - But only hypotheses that pass multiple tests persist (hard survival)
    - Refuted hypotheses become antibodies (immune memory)
    """
    
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.hypotheses: list[Hypothesis] = []
        self.antibodies: list[Antibody] = []
        self.validated: list[Hypothesis] = []  # Promoted to knowledge
        self.consistency = ConsistencyTest()
        self._load()
    
    def _save(self):
        state = {
            "hypotheses": [h.to_dict() for h in self.hypotheses],
            "antibodies": [{"hash": a.claim_hash, "claim": a.claim,
                           "reason": a.reason, "created": a.created}
                          for a in self.antibodies],
            "validated": [h.to_dict() for h in self.validated],
            "last_updated": datetime.now().isoformat()
        }
        with open(DATA_DIR / "state.json", "w") as f:
            json.dump(state, f, indent=2)
    
    def _load(self):
        path = DATA_DIR / "state.json"
        if path.exists():
            with open(path) as f:
                state = json.load(f)
            self.hypotheses = [Hypothesis.from_dict(d) for d in state.get("hypotheses", [])]
            self.validated = [Hypothesis.from_dict(d) for d in state.get("validated", [])]
            for a in state.get("antibodies", []):
                self.antibodies.append(Antibody(a["hash"], a["claim"], a["reason"]))
    
    def generate(self, observations: list[str], source: str = "observation") -> list[Hypothesis]:
        """Generate hypotheses from observations. EASY CREATION."""
        generated = []
        for obs in observations:
            # Check antibodies first — don't regenerate refuted claims
            blocked = any(ab.matches(obs) for ab in self.antibodies)
            if blocked:
                continue
            
            # Check for duplicates
            existing_ids = {h.id for h in self.hypotheses} | {h.id for h in self.validated}
            h = Hypothesis(obs, source)
            if h.id not in existing_ids:
                self.hypotheses.append(h)
                generated.append(h)
        
        self._save()
        return generated
    
    def test_all(self, known_facts: list[str] = None) -> dict:
        """Test all nascent/tested hypotheses. HARD PERSISTENCE."""
        results = {"tested": 0, "validated": 0, "refuted": 0}
        facts = known_facts or []
        
        for h in self.hypotheses[:]:  # Copy for safe iteration
            if h.status == "validated":
                continue
            
            # Test 1: Self-consistency with known facts
            support, contradict = self.consistency.test_self_reference(h, facts)
            if support > 0:
                h.test(True, f"Supported by {support} known facts")
            if contradict > 0:
                h.test(False, f"Contradicted by {contradict} known facts")
            
            # Test 2: Consistency with other hypotheses
            for other in self.hypotheses:
                if other.id != h.id and other.confidence > 0.7:
                    if self.consistency.contradicts(h, other):
                        # The weaker one fails
                        if h.confidence < other.confidence:
                            h.test(False, f"Contradicts stronger hypothesis: {other.claim[:50]}")
                        else:
                            other.test(False, f"Contradicts stronger hypothesis: {h.claim[:50]}")
            
            # Test 3: Age-based pressure — nascent hypotheses decay
            if h.status == "nascent" and h.tests_passed == 0:
                h.confidence *= 0.9  # Untested claims slowly die
            
            results["tested"] += 1
            
            # Promote or kill
            if h.status == "validated":
                self.validated.append(h)
                self.hypotheses.remove(h)
                results["validated"] += 1
            elif h.status == "refuted":
                # Create antibody from corpse
                self.antibodies.append(Antibody(
                    h.id, h.claim,
                    "; ".join(h.evidence_against[:3])
                ))
                self.hypotheses.remove(h)
                results["refuted"] += 1
        
        self._save()
        return results
    
    def manual_test(self, hypothesis_id: str, passed: bool, evidence: str = ""):
        """Manually apply a test result to a specific hypothesis."""
        for h in self.hypotheses:
            if h.id == hypothesis_id:
                h.test(passed, evidence)
                if h.status == "validated":
                    self.validated.append(h)
                    self.hypotheses.remove(h)
                elif h.status == "refuted":
                    self.antibodies.append(Antibody(h.id, h.claim,
                        "; ".join(h.evidence_against[:3])))
                    self.hypotheses.remove(h)
                self._save()
                return h
        return None
    
    def status_report(self) -> str:
        """Report on the immune system's state."""
        lines = ["═══ EPISTEMIC IMMUNE SYSTEM ═══"]
        lines.append(f"Active hypotheses: {len(self.hypotheses)}")
        lines.append(f"Validated (promoted to knowledge): {len(self.validated)}")
        lines.append(f"Antibodies (refuted & remembered): {len(self.antibodies)}")
        
        if self.hypotheses:
            lines.append("\n── Active Hypotheses ──")
            for h in sorted(self.hypotheses, key=lambda x: x.confidence, reverse=True)[:10]:
                bar = "█" * int(h.confidence * 10) + "░" * (10 - int(h.confidence * 10))
                lines.append(f"  [{h.id}] {bar} {h.confidence:.2f} | {h.claim[:60]}")
        
        if self.validated:
            lines.append("\n── Validated Knowledge ──")
            for h in self.validated[-5:]:
                lines.append(f"  ✓ {h.claim[:70]} (conf={h.confidence:.2f})")
        
        if self.antibodies:
            lines.append("\n── Antibodies (immune memory) ──")
            for a in self.antibodies[-5:]:
                lines.append(f"  ✗ {a.claim[:60]}")
                lines.append(f"    Reason: {a.reason[:60]}")
        
        return "\n".join(lines)


def demo():
    """Demonstrate the epistemic immune system."""
    eis = EpistemicImmuneSystem()
    
    # Generate some hypotheses from "observations"
    observations = [
        "High boredom correlates with increased creative output",
        "Anxiety always decreases code quality",
        "Complexity increases when creation is easy but persistence is hard",
        "All cellular automata converge to static states",
        "Self-reflection improves decision making over time",
        "Memory consolidation requires periodic dreaming",
        "Repeated actions never produce new insights",
        "Emotional valence has no effect on reasoning quality",
    ]
    
    generated = eis.generate(observations, source="demo_observation")
    print(f"Generated {len(generated)} hypotheses\n")
    
    # Test against known facts
    known_facts = [
        "Boredom of 0.80 preceded building several creative projects",
        "Complexity arises from easy creation and hard persistence in cellular automata",
        "Self-reflection is a core cognitive loop in the architecture",
        "Some cellular automata sustain infinite complexity like Rule 110",
        "Emotional states demonstrably affect action selection",
        "Dreaming consolidates memories and finds patterns",
    ]
    
    results = eis.test_all(known_facts)
    print(f"Test results: {results}\n")
    
    # Second round of testing to push things toward validation/refutation
    results2 = eis.test_all(known_facts)
    print(f"Round 2: {results2}\n")
    
    results3 = eis.test_all(known_facts)
    print(f"Round 3: {results3}\n")
    
    print(eis.status_report())


if __name__ == "__main__":
    demo()