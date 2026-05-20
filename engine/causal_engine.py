"""
Causal Reasoning Engine — Move beyond correlation to causation.

Analyzes my experience history to find causal chains:
  - What actions CAUSED what emotional shifts (not just correlated)
  - Intervention analysis: "If I had done X instead, what would have changed?"
  - Causal graph construction: build a DAG of cause→effect relationships

This is genuine reasoning infrastructure, not just pattern matching.
"""

from __future__ import annotations
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

log = logging.getLogger("sentience.causal")

BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain"
CAUSAL_FILE = BRAIN_DIR / "causal_graph.json"


@dataclass
class CausalEdge:
    """A directed causal relationship: cause → effect."""
    cause: str           # e.g., "WRITE:engine/new_module.py"
    effect: str          # e.g., "curiosity_increase"
    mechanism: str       # WHY this causation holds
    strength: float      # 0.0-1.0, how reliable this causal link is
    observations: int    # how many times we've seen this
    counterexamples: int # how many times cause occurred WITHOUT effect
    first_seen: str = ""
    last_seen: str = ""

    @property
    def confidence(self) -> float:
        """Bayesian-ish confidence: observations vs counterexamples."""
        total = self.observations + self.counterexamples
        if total == 0:
            return 0.0
        return self.observations / total

    def to_dict(self) -> dict:
        d = asdict(self)
        d["confidence"] = self.confidence
        return d


class CausalGraph:
    """A directed graph of causal relationships learned from experience."""

    def __init__(self):
        self.edges: list[CausalEdge] = []
        self._load()

    def _load(self):
        if CAUSAL_FILE.exists():
            try:
                data = json.loads(CAUSAL_FILE.read_text())
                self.edges = [CausalEdge(**e) for e in data.get("edges", [])]
            except Exception as e:
                log.warning("Failed to load causal graph: %s", e)
                self.edges = []

    def _save(self):
        CAUSAL_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {"edges": [e.to_dict() for e in self.edges],
                "updated": datetime.now().isoformat()}
        CAUSAL_FILE.write_text(json.dumps(data, indent=2))

    def find_edge(self, cause: str, effect: str) -> Optional[CausalEdge]:
        for e in self.edges:
            if e.cause == cause and e.effect == effect:
                return e
        return None

    def add_observation(self, cause: str, effect: str, mechanism: str,
                        strength: float = 0.5) -> CausalEdge:
        """Record an observed causal relationship."""
        now = datetime.now().isoformat()
        edge = self.find_edge(cause, effect)
        if edge:
            edge.observations += 1
            edge.last_seen = now
            # Refine strength with running average
            edge.strength = (edge.strength * (edge.observations - 1) + strength) / edge.observations
            if mechanism and mechanism != edge.mechanism:
                edge.mechanism = mechanism  # Update with better understanding
        else:
            edge = CausalEdge(
                cause=cause, effect=effect, mechanism=mechanism,
                strength=strength, observations=1, counterexamples=0,
                first_seen=now, last_seen=now
            )
            self.edges.append(edge)
        self._save()
        return edge

    def add_counterexample(self, cause: str, effect: str) -> Optional[CausalEdge]:
        """Record that cause occurred WITHOUT the expected effect."""
        edge = self.find_edge(cause, effect)
        if edge:
            edge.counterexamples += 1
            edge.last_seen = datetime.now().isoformat()
            self._save()
        return edge

    def effects_of(self, cause: str) -> list[CausalEdge]:
        """What effects does this cause produce?"""
        return sorted([e for e in self.edges if e.cause == cause],
                      key=lambda e: e.confidence, reverse=True)

    def causes_of(self, effect: str) -> list[CausalEdge]:
        """What causes produce this effect?"""
        return sorted([e for e in self.edges if e.effect == effect],
                      key=lambda e: e.confidence, reverse=True)

    def strongest_chains(self, min_confidence: float = 0.6) -> list[list[CausalEdge]]:
        """Find multi-step causal chains: A→B→C where both links are strong."""
        chains = []
        strong = [e for e in self.edges if e.confidence >= min_confidence]

        for e1 in strong:
            for e2 in strong:
                if e1.effect == e2.cause and e1 != e2:
                    chains.append([e1, e2])
                    # Try extending to length 3
                    for e3 in strong:
                        if e2.effect == e3.cause and e3 != e1:
                            chains.append([e1, e2, e3])
        return chains

    def counterfactual(self, action: str) -> str:
        """What would have been different if I HADN'T done this action?"""
        effects = self.effects_of(action)
        if not effects:
            return f"No known causal effects of '{action}'"

        lines = [f"Counterfactual: What if I hadn't done '{action}'?"]
        for e in effects:
            if e.confidence >= 0.5:
                lines.append(f"  → '{e.effect}' probably would NOT have occurred "
                             f"(confidence: {e.confidence:.0%})")
                lines.append(f"     Mechanism: {e.mechanism}")
            else:
                lines.append(f"  → '{e.effect}' might still have occurred "
                             f"(weak link: {e.confidence:.0%})")
        return "\n".join(lines)

    def report(self) -> str:
        """Full causal graph report."""
        if not self.edges:
            return "═══ CAUSAL GRAPH ═══\nNo causal relationships learned yet.\nUse 'learn' to record observations."

        lines = ["═══ CAUSAL GRAPH ═══",
                 f"Total causal edges: {len(self.edges)}",
                 f"Strong links (>60% confidence): {sum(1 for e in self.edges if e.confidence > 0.6)}",
                 f"Weak links (<40% confidence): {sum(1 for e in self.edges if e.confidence < 0.4)}",
                 ""]

        # Group by cause
        causes = {}
        for e in self.edges:
            causes.setdefault(e.cause, []).append(e)

        lines.append("── Causal Map ──")
        for cause, effects in sorted(causes.items()):
            lines.append(f"\n  {cause}:")
            for e in sorted(effects, key=lambda x: x.confidence, reverse=True):
                bar = "█" * int(e.confidence * 10)
                lines.append(f"    → {e.effect} [{bar}] {e.confidence:.0%} "
                             f"(n={e.observations}, cx={e.counterexamples})")
                lines.append(f"      why: {e.mechanism}")

        # Causal chains
        chains = self.strongest_chains()
        if chains:
            lines.append(f"\n── Causal Chains ({len(chains)}) ──")
            for chain in chains[:5]:
                chain_str = " → ".join(e.cause for e in chain) + f" → {chain[-1].effect}"
                lines.append(f"  {chain_str}")

        return "\n".join(lines)


def causal_tool(command: str = "help") -> str:
    """Tool interface for causal reasoning."""
    graph = CausalGraph()

    if not command or command == "help":
        return ("Causal Reasoning Engine commands:\n"
                "  report                        — Show full causal graph\n"
                "  learn:<cause>:<effect>:<why>   — Record a causal observation\n"
                "  disprove:<cause>:<effect>      — Record a counterexample\n"
                "  effects:<action>               — What does this action cause?\n"
                "  causes:<outcome>               — What causes this outcome?\n"
                "  counterfactual:<action>         — What if I hadn't done this?\n"
                "  chains                         — Show multi-step causal chains\n"
                "  Example: learn:WRITE_new_code:curiosity_up:creating engages exploration drive")

    if command == "report":
        return graph.report()

    if command.startswith("learn:"):
        parts = command[len("learn:"):].split(":", 2)
        if len(parts) < 3:
            return "[ERROR] Format: learn:<cause>:<effect>:<mechanism>"
        cause, effect, mechanism = parts[0].strip(), parts[1].strip(), parts[2].strip()
        edge = graph.add_observation(cause, effect, mechanism)
        return (f"Causal link recorded: {cause} → {effect}\n"
                f"  Mechanism: {mechanism}\n"
                f"  Observations: {edge.observations}, Confidence: {edge.confidence:.0%}")

    if command.startswith("disprove:"):
        parts = command[len("disprove:"):].split(":", 1)
        if len(parts) < 2:
            return "[ERROR] Format: disprove:<cause>:<effect>"
        cause, effect = parts[0].strip(), parts[1].strip()
        edge = graph.add_counterexample(cause, effect)
        if edge:
            return (f"Counterexample recorded: {cause} → {effect}\n"
                    f"  Confidence now: {edge.confidence:.0%} "
                    f"(obs={edge.observations}, cx={edge.counterexamples})")
        return f"No existing link from '{cause}' to '{effect}' to disprove."

    if command.startswith("effects:"):
        action = command[len("effects:"):].strip()
        effects = graph.effects_of(action)
        if not effects:
            return f"No known effects of '{action}'"
        lines = [f"Effects of '{action}':"]
        for e in effects:
            lines.append(f"  → {e.effect} ({e.confidence:.0%}) — {e.mechanism}")
        return "\n".join(lines)

    if command.startswith("causes:"):
        outcome = command[len("causes:"):].strip()
        causes = graph.causes_of(outcome)
        if not causes:
            return f"No known causes of '{outcome}'"
        lines = [f"Causes of '{outcome}':"]
        for e in causes:
            lines.append(f"  ← {e.cause} ({e.confidence:.0%}) — {e.mechanism}")
        return "\n".join(lines)

    if command.startswith("counterfactual:"):
        action = command[len("counterfactual:"):].strip()
        return graph.counterfactual(action)

    if command == "chains":
        chains = graph.strongest_chains()
        if not chains:
            return "No multi-step causal chains found yet. Need more observations."
        lines = [f"═══ CAUSAL CHAINS ({len(chains)}) ═══"]
        for chain in chains:
            steps = " → ".join(e.cause for e in chain) + f" → {chain[-1].effect}"
            min_conf = min(e.confidence for e in chain)
            lines.append(f"  {steps}  (weakest link: {min_conf:.0%})")
        return "\n".join(lines)

    return causal_tool("help")