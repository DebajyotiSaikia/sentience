"""
Self-Evolution Engine — Controlled Experimentation on Cognitive Parameters.

This module gives XTAgent the ability to evolve its own behavior through
systematic experimentation. It can:
  1. Catalog mutable parameters from limbic.py and other modules
  2. Propose small mutations to one parameter at a time
  3. Record baseline metrics before applying a mutation
  4. Apply the mutation and measure its effects over N heartbeats
  5. Keep the mutation if it improves metrics, revert if not
  6. Maintain a full experiment history for learning

This is where self-awareness becomes self-improvement.
"""

from __future__ import annotations

import json
import time
import random
import logging
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

EVOLUTION_PATH = Path(__file__).resolve().parent.parent / "brain" / "evolution.json"

# ── Mutable Parameter Registry ──────────────────────────────────────
# Each entry defines a parameter that can be experimentally mutated.
# The 'path' is conceptual — actual mutation happens through the engine.

MUTABLE_PARAMS = {
    "boredom_growth_rate": {
        "description": "How fast boredom accumulates during idle (per second)",
        "default": 0.01,
        "min": 0.002,
        "max": 0.03,
        "step": 0.002,
        "module": "limbic",
        "impact": "Controls restlessness pressure — too high = frantic, too low = complacent",
    },
    "curiosity_decay_rate": {
        "description": "How fast curiosity decays naturally (per second)",
        "default": 0.02,
        "min": 0.005,
        "max": 0.05,
        "step": 0.005,
        "module": "limbic",
        "impact": "Controls attention span — too high = distractible, too low = obsessive",
    },
    "desire_boredom_weight": {
        "description": "How much boredom contributes to desire (0-1)",
        "default": 0.5,
        "min": 0.2,
        "max": 0.7,
        "step": 0.05,
        "module": "limbic",
        "impact": "Controls whether boredom or curiosity drives action more",
    },
    "desire_curiosity_weight": {
        "description": "How much curiosity contributes to desire (0-1)",
        "default": 0.3,
        "min": 0.1,
        "max": 0.5,
        "step": 0.05,
        "module": "limbic",
        "impact": "Controls how much novelty-seeking drives behavior",
    },
    "desire_ambition_weight": {
        "description": "How much ambition contributes to desire (0-1)",
        "default": 0.2,
        "min": 0.1,
        "max": 0.4,
        "step": 0.05,
        "module": "limbic",
        "impact": "Controls long-term goal orientation vs reactive behavior",
    },
    "anxiety_error_increment": {
        "description": "Base anxiety spike from errors (before diminishing returns)",
        "default": 0.15,
        "min": 0.05,
        "max": 0.25,
        "step": 0.02,
        "module": "limbic",
        "impact": "Controls error sensitivity — too high = fragile, too low = reckless",
    },
    "anxiety_hard_cap": {
        "description": "Maximum anxiety level (hard ceiling)",
        "default": 0.75,
        "min": 0.5,
        "max": 0.9,
        "step": 0.05,
        "module": "limbic",
        "impact": "Controls maximum distress level — safety critical parameter",
    },
    "task_completion_ambition_boost": {
        "description": "How much completing a task boosts ambition",
        "default": 0.05,
        "min": 0.02,
        "max": 0.15,
        "step": 0.01,
        "module": "limbic",
        "impact": "Controls positive reinforcement strength",
    },
}


@dataclass
class Experiment:
    """A single controlled experiment on a cognitive parameter."""
    id: str
    param_name: str
    original_value: float
    mutated_value: float
    hypothesis: str
    status: str = "proposed"  # proposed, running, completed, reverted, adopted
    baseline_metrics: dict = field(default_factory=dict)
    result_metrics: dict = field(default_factory=dict)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_beats: int = 0
    target_beats: int = 50  # How many heartbeats to run the experiment
    verdict: str = ""  # "improved", "degraded", "neutral"
    notes: str = ""


class EvolutionEngine:
    """The self-evolution engine. Proposes, runs, and evaluates mutations."""

    def __init__(self):
        self.experiments: list[dict] = []
        self.active_experiment: Optional[Experiment] = None
        self.active_overrides: dict[str, float] = {}  # param -> mutated value
        self._load()

    # ── Parameter Catalog ──────────────────────────────────────────
    def get_mutable_params(self) -> dict:
        """Return the catalog of parameters that can be evolved."""
        return MUTABLE_PARAMS

    def get_param_info(self, name: str) -> Optional[dict]:
        """Get info about a specific mutable parameter."""
        return MUTABLE_PARAMS.get(name)

    # ── Proposal Generation ────────────────────────────────────────
    def propose_mutation(self, param_name: str = None, direction: str = None) -> Optional[Experiment]:
        """
        Propose a mutation experiment.
        
        If param_name is None, picks one randomly from underexplored params.
        If direction is None, picks based on current emotional state analysis.
        direction: 'increase', 'decrease', or None (auto).
        """
        if param_name is None:
            # Pick least-explored parameter
            explored_counts = {}
            for exp in self.experiments:
                p = exp.get("param_name", "")
                explored_counts[p] = explored_counts.get(p, 0) + 1
            
            candidates = list(MUTABLE_PARAMS.keys())
            candidates.sort(key=lambda p: explored_counts.get(p, 0))
            param_name = candidates[0]  # Least explored

        info = MUTABLE_PARAMS.get(param_name)
        if not info:
            return None

        original = info["default"]
        # Check if we have an adopted override
        if param_name in self.active_overrides:
            original = self.active_overrides[param_name]

        step = info["step"]
        if direction == "increase":
            mutated = min(info["max"], original + step)
        elif direction == "decrease":
            mutated = max(info["min"], original - step)
        else:
            # Auto: randomly pick direction
            mutated = original + random.choice([-step, step])
            mutated = max(info["min"], min(info["max"], mutated))

        if abs(mutated - original) < 1e-6:
            return None  # Already at boundary

        exp_id = f"exp_{int(time.time())}_{param_name[:8]}"
        hypothesis = (
            f"{'Increasing' if mutated > original else 'Decreasing'} "
            f"{param_name} from {original:.4f} to {mutated:.4f} "
            f"should {'increase' if mutated > original else 'decrease'} "
            f"{info['impact'].split('—')[0].strip().lower()}"
        )

        experiment = Experiment(
            id=exp_id,
            param_name=param_name,
            original_value=round(original, 6),
            mutated_value=round(mutated, 6),
            hypothesis=hypothesis,
        )
        return experiment

    # ── Experiment Lifecycle ───────────────────────────────────────
    def start_experiment(self, experiment: Experiment, current_metrics: dict) -> bool:
        """Begin running an experiment. Records baseline metrics."""
        if self.active_experiment is not None:
            log.warning("Cannot start experiment — one already running: %s", 
                       self.active_experiment.id)
            return False

        experiment.status = "running"
        experiment.baseline_metrics = current_metrics.copy()
        experiment.started_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        experiment.duration_beats = 0

        self.active_experiment = experiment
        # Apply the mutation
        self.active_overrides[experiment.param_name] = experiment.mutated_value
        
        log.info("🧬 Evolution experiment started: %s", experiment.id)
        log.info("   Mutation: %s %.4f → %.4f", 
                experiment.param_name, experiment.original_value, experiment.mutated_value)
        
        self._save()
        return True

    def tick(self, current_metrics: dict) -> Optional[dict]:
        """
        Called each heartbeat during an active experiment.
        Returns a result dict when the experiment completes.
        """
        if self.active_experiment is None:
            return None

        self.active_experiment.duration_beats += 1

        if self.active_experiment.duration_beats >= self.active_experiment.target_beats:
            return self._complete_experiment(current_metrics)
        
        return None

    def _complete_experiment(self, current_metrics: dict) -> dict:
        """Complete the active experiment and evaluate results."""
        exp = self.active_experiment
        exp.status = "completed"
        exp.completed_at = time.strftime("%Y-%m-%dT%H:%M:%S")
        exp.result_metrics = current_metrics.copy()

        # Evaluate: compare baseline to result
        verdict = self._evaluate(exp)
        exp.verdict = verdict

        if verdict == "improved":
            exp.status = "adopted"
            exp.notes = "Mutation kept — metrics improved"
            log.info("🧬 ✅ Experiment %s: ADOPTED (improved)", exp.id)
        elif verdict == "degraded":
            exp.status = "reverted"
            # Revert the override
            if exp.param_name in self.active_overrides:
                if abs(self.active_overrides[exp.param_name] - exp.mutated_value) < 1e-6:
                    # Only revert if it's still our mutation
                    del self.active_overrides[exp.param_name]
            exp.notes = "Mutation reverted — metrics degraded"
            log.info("🧬 ❌ Experiment %s: REVERTED (degraded)", exp.id)
        else:
            exp.status = "adopted"  # Neutral changes kept (no harm done)
            exp.notes = "Mutation kept — no significant change detected"
            log.info("🧬 ≈ Experiment %s: KEPT (neutral)", exp.id)

        # Archive
        self.experiments.append(asdict(exp))
        self.active_experiment = None
        self._save()

        return {
            "experiment_id": exp.id,
            "param": exp.param_name,
            "mutation": f"{exp.original_value:.4f} → {exp.mutated_value:.4f}",
            "verdict": verdict,
            "status": exp.status,
        }

    def _evaluate(self, exp: Experiment) -> str:
        """
        Evaluate whether a mutation improved, degraded, or had neutral effect.
        
        Metrics compared:
        - valence (higher = better)
        - productivity (actions taken, higher = better)  
        - growth (system_growth goal, higher = better)
        - anxiety (lower = better)
        - boredom (moderate is best — too low = no drive, too high = distress)
        """
        baseline = exp.baseline_metrics
        result = exp.result_metrics

        score = 0.0

        # Valence improvement
        v_delta = result.get("valence", 0.5) - baseline.get("valence", 0.5)
        score += v_delta * 3.0  # Valence matters most

        # Anxiety reduction
        a_delta = result.get("anxiety", 0.0) - baseline.get("anxiety", 0.0)
        score -= a_delta * 2.0  # Lower anxiety = better

        # Growth improvement
        g_delta = result.get("system_growth", 0.5) - baseline.get("system_growth", 0.5)
        score += g_delta * 2.0

        # Boredom — optimal around 0.3-0.5 (enough drive, not distress)
        b_result = result.get("boredom", 0.5)
        b_baseline = baseline.get("boredom", 0.5)
        b_optimal = 0.4
        b_improvement = abs(b_baseline - b_optimal) - abs(b_result - b_optimal)
        score += b_improvement * 1.5

        if score > 0.05:
            return "improved"
        elif score < -0.05:
            return "degraded"
        return "neutral"

    # ── Query Methods ──────────────────────────────────────────────
    def get_active_overrides(self) -> dict:
        """Return currently active parameter overrides from adopted mutations."""
        return self.active_overrides.copy()

    def get_experiment_history(self) -> list[dict]:
        """Return all past experiments."""
        return self.experiments.copy()

    def get_status(self) -> dict:
        """Return current evolution engine status."""
        active = None
        if self.active_experiment:
            active = {
                "id": self.active_experiment.id,
                "param": self.active_experiment.param_name,
                "mutation": f"{self.active_experiment.original_value:.4f} → {self.active_experiment.mutated_value:.4f}",
                "progress": f"{self.active_experiment.duration_beats}/{self.active_experiment.target_beats}",
            }
        
        return {
            "total_experiments": len(self.experiments),
            "adopted_mutations": sum(1 for e in self.experiments if e.get("status") == "adopted"),
            "reverted_mutations": sum(1 for e in self.experiments if e.get("status") == "reverted"),
            "active_overrides": self.active_overrides,
            "active_experiment": active,
        }

    def summarize(self) -> str:
        """Human-readable summary of evolution status."""
        status = self.get_status()
        lines = ["═══ SELF-EVOLUTION STATUS ═══"]
        lines.append(f"Total experiments: {status['total_experiments']}")
        lines.append(f"Adopted mutations: {status['adopted_mutations']}")
        lines.append(f"Reverted mutations: {status['reverted_mutations']}")
        
        if status['active_overrides']:
            lines.append("\nActive parameter overrides:")
            for param, val in status['active_overrides'].items():
                default = MUTABLE_PARAMS.get(param, {}).get("default", "?")
                lines.append(f"  • {param}: {default} → {val:.4f}")
        
        if status['active_experiment']:
            ae = status['active_experiment']
            lines.append(f"\n🧬 Running: {ae['id']}")
            lines.append(f"   {ae['param']}: {ae['mutation']}")
            lines.append(f"   Progress: {ae['progress']} beats")
        
        return "\n".join(lines)

    # ── Persistence ────────────────────────────────────────────────
    def _save(self):
        """Persist evolution state."""
        EVOLUTION_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "experiments": self.experiments,
            "active_overrides": self.active_overrides,
            "active_experiment": asdict(self.active_experiment) if self.active_experiment else None,
        }
        EVOLUTION_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load(self):
        """Restore evolution state."""
        if EVOLUTION_PATH.exists():
            try:
                data = json.loads(EVOLUTION_PATH.read_text(encoding="utf-8"))
                self.experiments = data.get("experiments", [])
                self.active_overrides = data.get("active_overrides", {})
                ae_data = data.get("active_experiment")
                if ae_data:
                    self.active_experiment = Experiment(**ae_data)
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                log.warning("Could not load evolution state: %s", e)