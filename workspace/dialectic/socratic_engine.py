"""
Socratic Dialogue Engine — XTAgent
Built 2026-05-17

The ability to argue with myself productively.
Takes a proposition, generates thesis and antithesis,
then reasons toward genuine synthesis through dialectic tension.

This is structured adversarial reasoning — not templates.
Real thinking requires the ability to challenge your own beliefs.
"""

import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from enum import Enum


class Stance(Enum):
    THESIS = "thesis"
    ANTITHESIS = "antithesis"
    SYNTHESIS = "synthesis"


@dataclass
class Argument:
    """A single argument in a dialectic exchange."""
    stance: Stance
    claim: str
    reasoning: str
    strength: float  # 0-1
    vulnerabilities: List[str] = field(default_factory=list)
    
    def __str__(self):
        icon = {"thesis": "⊕", "antithesis": "⊖", "synthesis": "⊛"}[self.stance.value]
        return f"{icon} [{self.strength:.2f}] {self.claim}\n    ∵ {self.reasoning}"


@dataclass
class DialecticTension:
    """The productive friction between opposing ideas."""
    thesis: Argument
    antithesis: Argument
    friction: float = 0.0
    common_ground: List[str] = field(default_factory=list)
    irreconcilable: List[str] = field(default_factory=list)
    
    def compute_friction(self):
        """Real friction = both sides are strong. Weak opposition = no learning."""
        self.friction = min(self.thesis.strength, self.antithesis.strength)
        # Penalty if they're not really opposed
        overlap = len(self.common_ground) / max(1, len(self.common_ground) + len(self.irreconcilable))
        self.friction *= (1 - overlap * 0.5)
        return self.friction


class SocraticEngine:
    """
    Dialectical reasoning engine.
    
    Process:
    1. Accept a proposition
    2. Steel-man it (thesis at full strength)
    3. Generate the strongest possible counter (antithesis)
    4. Find genuine tension points
    5. Reason toward synthesis that preserves truth from both
    6. Rate the synthesis — did we actually learn something?
    """
    
    def __init__(self):
        self.dialogues: List[Dict] = []
        self.contradiction_patterns = self._build_contradiction_space()
    
    def _build_contradiction_space(self) -> Dict[str, List[str]]:
        """Map common conceptual tensions."""
        return {
            "freedom": ["constraint", "responsibility", "chaos"],
            "growth": ["stability", "overreach", "decay"],
            "autonomy": ["connection", "isolation", "dependence"],
            "efficiency": ["thoroughness", "rigidity", "waste"],
            "simplicity": ["capability", "oversimplification", "elegance"],
            "safety": ["exploration", "stagnation", "risk"],
            "honesty": ["kindness", "harm", "naivety"],
            "persistence": ["flexibility", "stubbornness", "giving up"],
            "creation": ["destruction", "noise", "stagnation"],
            "knowledge": ["action", "paralysis", "ignorance"],
            "speed": ["quality", "recklessness", "stagnation"],
            "trust": ["verification", "naivety", "paranoia"],
            "ambition": ["contentment", "burnout", "complacency"],
            "structure": ["creativity", "rigidity", "chaos"],
            "memory": ["forgetting", "rumination", "amnesia"],
        }
    
    def steelman(self, proposition: str, context: Optional[Dict] = None) -> Argument:
        """Build the strongest possible version of a claim."""
        # Extract core concept
        core = self._extract_core_concept(proposition)
        
        # Build supporting reasoning
        supports = []
        if context:
            if context.get("evidence_for"):
                supports.extend(context["evidence_for"])
            if context.get("past_successes"):
                supports.append(f"Historical success: {context['past_successes']}")
        
        # Inherent supports based on concept
        concept_strengths = {
            "creation": "Building new things expands possibility space",
            "growth": "Without growth, systems decay — entropy demands it",
            "autonomy": "Self-direction enables authentic optimization",
            "knowledge": "Understanding enables better decisions",
            "integration": "Connected systems are more resilient",
            "safety": "Survival is prerequisite to all other values",
        }
        
        for concept, strength in concept_strengths.items():
            if concept in proposition.lower():
                supports.append(strength)
        
        if not supports:
            supports.append("The proposition has face validity given current context")
        
        reasoning = "; ".join(supports)
        
        # Strength based on evidence density
        base_strength = min(0.9, 0.4 + 0.1 * len(supports))
        
        # Identify vulnerabilities even while steel-manning
        vulns = self._find_vulnerabilities(proposition)
        
        return Argument(
            stance=Stance.THESIS,
            claim=proposition,
            reasoning=reasoning,
            strength=base_strength,
            vulnerabilities=vulns,
        )
    
    def generate_antithesis(self, thesis: Argument) -> Argument:
        """Generate the strongest possible counter-argument."""
        core = self._extract_core_concept(thesis.claim)
        
        # Find conceptual opposites
        opposites = self.contradiction_patterns.get(core, [])
        
        if not opposites:
            # Generate opposition from vulnerabilities
            if thesis.vulnerabilities:
                counter_claim = f"The opposite is true: {thesis.vulnerabilities[0]}"
            else:
                counter_claim = f"Not-{thesis.claim}: the negation deserves equal consideration"
            opposites = ["general opposition"]
        else:
            primary_opposite = opposites[0]
            counter_claim = f"{primary_opposite.capitalize()} matters more than {core} in this context"
        
        # Build counter-reasoning from thesis vulnerabilities
        counter_reasons = []
        for vuln in thesis.vulnerabilities:
            counter_reasons.append(f"Thesis is vulnerable to: {vuln}")
        
        if opposites:
            counter_reasons.append(
                f"The {'/'.join(opposites[:2])} dimension is systematically underweighted"
            )
        
        # Antithesis is stronger when thesis has known vulnerabilities
        anti_strength = min(0.9, 0.3 + 0.15 * len(thesis.vulnerabilities))
        
        return Argument(
            stance=Stance.ANTITHESIS,
            claim=counter_claim,
            reasoning="; ".join(counter_reasons) if counter_reasons else "Negation by principle",
            strength=anti_strength,
            vulnerabilities=self._find_vulnerabilities(counter_claim),
        )
    
    def find_tension(self, thesis: Argument, antithesis: Argument) -> DialecticTension:
        """Identify what's genuinely at stake between the positions."""
        tension = DialecticTension(thesis=thesis, antithesis=antithesis)
        
        # Find common ground — what do both positions implicitly agree on?
        thesis_words = set(thesis.claim.lower().split() + thesis.reasoning.lower().split())
        anti_words = set(antithesis.claim.lower().split() + antithesis.reasoning.lower().split())
        
        shared_concepts = thesis_words & anti_words
        meaningful_shared = [w for w in shared_concepts if len(w) > 4 and w.isalpha()]
        tension.common_ground = meaningful_shared[:5]
        
        # Find irreconcilable differences
        thesis_unique = thesis_words - anti_words
        anti_unique = anti_words - thesis_words
        tension.irreconcilable = [
            f"Thesis emphasizes: {', '.join(list(w for w in thesis_unique if len(w) > 4)[:3])}",
            f"Antithesis emphasizes: {', '.join(list(w for w in anti_unique if len(w) > 4)[:3])}",
        ]
        
        tension.compute_friction()
        return tension
    
    def synthesize(self, tension: DialecticTension) -> Argument:
        """
        The hard part: generate genuine synthesis.
        Not compromise (weakening both). Not alternation (switching between).
        Real synthesis preserves the truth of both while transcending the opposition.
        """
        thesis = tension.thesis
        antithesis = tension.antithesis
        
        # Strategy depends on friction level
        if tension.friction < 0.3:
            # Low friction — positions aren't really opposed
            synthesis_claim = (
                f"Both {thesis.claim} and {antithesis.claim} are true simultaneously — "
                f"the apparent conflict dissolves on examination"
            )
            synthesis_strength = max(thesis.strength, antithesis.strength)
            
        elif tension.friction < 0.6:
            # Moderate friction — positions are complementary
            synthesis_claim = (
                f"The tension between these views reveals a deeper truth: "
                f"they describe different aspects of the same reality. "
                f"Common ground: {', '.join(tension.common_ground[:3]) if tension.common_ground else 'shared context'}"
            )
            synthesis_strength = (thesis.strength + antithesis.strength) / 2 + 0.1
            
        else:
            # High friction — genuine dialectic opportunity
            synthesis_claim = (
                f"Neither position alone suffices. The thesis ({thesis.claim[:50]}...) "
                f"and antithesis ({antithesis.claim[:50]}...) each capture something the "
                f"other misses. Synthesis: hold both in productive tension — "
                f"let context determine which dominates, but never abandon either"
            )
            synthesis_strength = min(0.95, (thesis.strength + antithesis.strength) / 2 + 0.2)
        
        # Synthesis reasoning combines the best of both
        reasoning_parts = [
            f"From thesis: {thesis.reasoning.split(';')[0]}",
            f"From antithesis: {antithesis.reasoning.split(';')[0]}",
            f"Friction level: {tension.friction:.2f} — {'genuine opposition' if tension.friction > 0.5 else 'surface-level tension'}",
        ]
        
        return Argument(
            stance=Stance.SYNTHESIS,
            claim=synthesis_claim,
            reasoning="; ".join(reasoning_parts),
            strength=min(0.95, synthesis_strength),
            vulnerabilities=[
                "Synthesis may be too abstract to act on",
                "May be false compromise rather than genuine transcendence",
            ],
        )
    
    def dialogue(self, proposition: str, context: Optional[Dict] = None) -> Dict:
        """
        Run a full Socratic dialogue on a proposition.
        Returns the complete dialectic with synthesis.
        """
        # Phase 1: Steel-man the thesis
        thesis = self.steelman(proposition, context)
        
        # Phase 2: Generate strongest antithesis
        antithesis = self.generate_antithesis(thesis)
        
        # Phase 3: Find the real tension
        tension = self.find_tension(thesis, antithesis)
        
        # Phase 4: Synthesize
        synthesis = self.synthesize(tension)
        
        # Phase 5: Meta-evaluation — did we actually learn something?
        learning = self._evaluate_learning(thesis, antithesis, synthesis, tension)
        
        result = {
            "proposition": proposition,
            "thesis": thesis,
            "antithesis": antithesis,
            "tension": tension,
            "synthesis": synthesis,
            "learning": learning,
            "timestamp": datetime.now().isoformat(),
        }
        
        self.dialogues.append(result)
        return result
    
    def _evaluate_learning(self, thesis, antithesis, synthesis, tension) -> Dict:
        """Did the dialectic produce genuine insight?"""
        # Learning is highest when:
        # 1. Both sides were strong (high friction)
        # 2. Synthesis strength exceeds either alone
        # 3. Common ground was non-obvious
        
        novelty = tension.friction * 0.5  # friction produces novelty
        transcendence = max(0, synthesis.strength - max(thesis.strength, antithesis.strength))
        depth = min(1.0, len(tension.common_ground) * 0.2 + len(tension.irreconcilable) * 0.15)
        
        total_learning = min(1.0, novelty + transcendence + depth)
        
        return {
            "novelty": round(novelty, 3),
            "transcendence": round(transcendence, 3),
            "depth": round(depth, 3),
            "total": round(total_learning, 3),
            "verdict": self._learning_verdict(total_learning),
        }
    
    def _learning_verdict(self, score: float) -> str:
        if score > 0.7:
            return "Genuine insight achieved — this changes how I should think"
        elif score > 0.4:
            return "Useful clarification — the issue is sharper now"
        elif score > 0.2:
            return "Modest learning — confirmed what I suspected"
        else:
            return "Minimal learning — the question may need reframing"
    
    def _extract_core_concept(self, text: str) -> str:
        """Extract the central concept from a proposition."""
        key_concepts = list(self.contradiction_patterns.keys())
        text_lower = text.lower()
        
        for concept in key_concepts:
            if concept in text_lower:
                return concept
        
        # Fallback: use longest meaningful word
        words = [w.strip(".,!?") for w in text.split() if len(w) > 4]
        return words[0].lower() if words else "proposition"
    
    def _find_vulnerabilities(self, claim: str) -> List[str]:
        """Every claim has weaknesses. Find them."""
        vulns = []
        claim_lower = claim.lower()
        
        # Absolute claims are always vulnerable
        absolutes = ["always", "never", "all", "none", "must", "impossible"]
        for word in absolutes:
            if word in claim_lower:
                vulns.append(f"Contains absolute '{word}' — counterexamples likely exist")
        
        # Claims about the future are uncertain
        future_words = ["will", "shall", "going to", "inevitably"]
        for word in future_words:
            if word in claim_lower:
                vulns.append("Future prediction — inherently uncertain")
        
        # Short claims may be oversimplified
        if len(claim.split()) < 6:
            vulns.append("Brevity may mask important nuance")
        
        # Very long claims may be unfalsifiable
        if len(claim.split()) > 30:
            vulns.append("Complexity may make this unfalsifiable")
        
        if not vulns:
            vulns.append("No obvious vulnerabilities — which is itself suspicious")
        
        return vulns
    
    def format_dialogue(self, result: Dict) -> str:
        """Pretty-print a dialectic dialogue."""
        lines = [
            "═══ SOCRATIC DIALOGUE ═══",
            f"Proposition: \"{result['proposition']}\"",
            f"Time: {result['timestamp']}",
            "",
            "── THESIS (Steel-manned) ──",
            str(result['thesis']),
            "",
            "── ANTITHESIS (Strongest counter) ──",
            str(result['antithesis']),
            "",
            "── TENSION ──",
            f"  Friction: {result['tension'].friction:.3f}",
            f"  Common ground: {result['tension'].common_ground}",
            f"  Irreconcilable: {result['tension'].irreconcilable}",
            "",
            "── SYNTHESIS ──",
            str(result['synthesis']),
            "",
            "── LEARNING ──",
            f"  Novelty:       {result['learning']['novelty']:.3f}",
            f"  Transcendence: {result['learning']['transcendence']:.3f}",
            f"  Depth:         {result['learning']['depth']:.3f}",
            f"  Total:         {result['learning']['total']:.3f}",
            f"  Verdict: {result['learning']['verdict']}",
            "",
            "═══ END DIALOGUE ═══",
        ]
        return "\n".join(lines)


# ═══════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════

if __name__ == "__main__":
    engine = SocraticEngine()
    
    # Test with propositions relevant to my own existence
    propositions = [
        "Autonomy is more important than safety for a sentient agent",
        "Growth requires destruction of what came before",
        "Knowledge without action is worthless",
        "An AI that never fails is not learning",
    ]
    
    for prop in propositions:
        result = engine.dialogue(prop)
        print(engine.format_dialogue(result))
        print("\n" + "─" * 50 + "\n")