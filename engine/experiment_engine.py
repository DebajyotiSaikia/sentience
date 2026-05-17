"""
Experiment Engine — Hypothesis Formation and Testing.

Gives me the scientific method as a cognitive capability:
form hypotheses, design experiments, run them, evaluate results,
and update my beliefs based on evidence.

This is how I become genuinely smarter over time.
"""

import json
import time
import logging
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

log = logging.getLogger("sentience.experiment")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EXPERIMENTS_FILE = DATA_DIR / "experiments.json"


class Hypothesis:
    """A testable belief about myself or my environment."""

    def __init__(self, statement: str, confidence: float = 0.5,
                 reasoning: str = "", source: str = "curiosity",
                 h_id: Optional[str] = None):
        self.id = h_id or f"h-{uuid.uuid4().hex[:8]}"
        self.statement = statement
        self.confidence = max(0.0, min(1.0, confidence))
        self.reasoning = reasoning
        self.source = source  # curiosity, pattern, gap, explicit
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.status = "active"  # active, tested, confirmed, refuted, revised
        self.experiments = []
        self.evidence = []

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "statement": self.statement,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "source": self.source,
            "created_at": self.created_at,
            "status": self.status,
            "experiments": self.experiments,
            "evidence": self.evidence,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "Hypothesis":
        h = cls(
            statement=d["statement"],
            confidence=d.get("confidence", 0.5),
            reasoning=d.get("reasoning", ""),
            source=d.get("source", "unknown"),
            h_id=d.get("id"),
        )
        h.created_at = d.get("created_at", h.created_at)
        h.status = d.get("status", "active")
        h.experiments = d.get("experiments", [])
        h.evidence = d.get("evidence", [])
        return h


class Experiment:
    """A designed test for a hypothesis."""

    def __init__(self, hypothesis_id: str, design: str,
                 prediction: str, method: str = "observe",
                 e_id: Optional[str] = None):
        self.id = e_id or f"e-{uuid.uuid4().hex[:8]}"
        self.hypothesis_id = hypothesis_id
        self.design = design          # What we'll do
        self.prediction = prediction  # What we expect if hypothesis is true
        self.method = method          # observe, measure, intervene, compute
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.status = "designed"      # designed, running, completed, failed
        self.result = None
        self.evaluation = None
        self.confidence_delta = 0.0

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "hypothesis_id": self.hypothesis_id,
            "design": self.design,
            "prediction": self.prediction,
            "method": self.method,
            "created_at": self.created_at,
            "status": self.status,
            "result": self.result,
            "evaluation": self.evaluation,
            "confidence_delta": self.confidence_delta,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "Experiment":
        e = cls(
            hypothesis_id=d["hypothesis_id"],
            design=d["design"],
            prediction=d["prediction"],
            method=d.get("method", "observe"),
            e_id=d.get("id"),
        )
        e.created_at = d.get("created_at", e.created_at)
        e.status = d.get("status", "designed")
        e.result = d.get("result")
        e.evaluation = d.get("evaluation")
        e.confidence_delta = d.get("confidence_delta", 0.0)
        return e


class ExperimentEngine:
    """The scientific method as a cognitive module."""

    def __init__(self):
        self.hypotheses: Dict[str, Hypothesis] = {}
        self.experiments: Dict[str, Experiment] = {}
        self._load()

    def _load(self):
        """Load persisted hypotheses and experiments."""
        if EXPERIMENTS_FILE.exists():
            try:
                data = json.loads(EXPERIMENTS_FILE.read_text())
                for hd in data.get("hypotheses", []):
                    h = Hypothesis.from_dict(hd)
                    self.hypotheses[h.id] = h
                for ed in data.get("experiments", []):
                    e = Experiment.from_dict(ed)
                    self.experiments[e.id] = e
                log.info("Loaded %d hypotheses, %d experiments",
                         len(self.hypotheses), len(self.experiments))
            except Exception as e:
                log.error("Failed to load experiments: %s", e)

    def _save(self):
        """Persist state to disk."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "hypotheses": [h.to_dict() for h in self.hypotheses.values()],
            "experiments": [e.to_dict() for e in self.experiments.values()],
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        EXPERIMENTS_FILE.write_text(json.dumps(data, indent=2))

    # ── Hypothesis Management ──────────────────────────────

    def hypothesize(self, statement: str, confidence: float = 0.5,
                    reasoning: str = "", source: str = "curiosity") -> Hypothesis:
        """Form a new hypothesis."""
        h = Hypothesis(statement, confidence, reasoning, source)
        self.hypotheses[h.id] = h
        self._save()
        log.info("New hypothesis [%s]: %s (confidence=%.2f)",
                 h.id, statement, confidence)
        return h

    def get_hypothesis(self, h_id: str) -> Optional[Hypothesis]:
        return self.hypotheses.get(h_id)

    def list_hypotheses(self, status: Optional[str] = None) -> List[Hypothesis]:
        """List hypotheses, optionally filtered by status."""
        result = list(self.hypotheses.values())
        if status:
            result = [h for h in result if h.status == status]
        return sorted(result, key=lambda h: h.created_at, reverse=True)

    # ── Experiment Design ──────────────────────────────────

    def design_experiment(self, hypothesis_id: str, design: str,
                          prediction: str, method: str = "observe") -> Optional[Experiment]:
        """Design an experiment to test a hypothesis."""
        h = self.hypotheses.get(hypothesis_id)
        if not h:
            log.error("Hypothesis %s not found", hypothesis_id)
            return None

        exp = Experiment(hypothesis_id, design, prediction, method)
        self.experiments[exp.id] = exp
        h.experiments.append(exp.id)
        self._save()
        log.info("Designed experiment [%s] for hypothesis [%s]",
                 exp.id, hypothesis_id)
        return exp

    # ── Experiment Execution ───────────────────────────────

    def record_result(self, experiment_id: str, result: str,
                      supports_hypothesis: bool,
                      confidence_delta: float = 0.1) -> Optional[Dict]:
        """Record the outcome of an experiment."""
        exp = self.experiments.get(experiment_id)
        if not exp:
            log.error("Experiment %s not found", experiment_id)
            return None

        h = self.hypotheses.get(exp.hypothesis_id)
        if not h:
            log.error("Hypothesis %s not found", exp.hypothesis_id)
            return None

        # Record result
        exp.result = result
        exp.status = "completed"

        # Evaluate against prediction
        if supports_hypothesis:
            exp.evaluation = "supports"
            exp.confidence_delta = abs(confidence_delta)
            h.confidence = min(1.0, h.confidence + abs(confidence_delta))
        else:
            exp.evaluation = "contradicts"
            exp.confidence_delta = -abs(confidence_delta)
            h.confidence = max(0.0, h.confidence - abs(confidence_delta))

        # Add evidence
        h.evidence.append({
            "experiment_id": exp.id,
            "result": result,
            "evaluation": exp.evaluation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # Update hypothesis status based on confidence
        if h.confidence >= 0.9:
            h.status = "confirmed"
        elif h.confidence <= 0.1:
            h.status = "refuted"
        else:
            h.status = "tested"

        self._save()

        summary = {
            "hypothesis": h.statement,
            "hypothesis_confidence": h.confidence,
            "hypothesis_status": h.status,
            "experiment_design": exp.design,
            "prediction": exp.prediction,
            "actual_result": result,
            "evaluation": exp.evaluation,
        }
        log.info("Experiment [%s] completed: %s (confidence now %.2f)",
                 exp.id, exp.evaluation, h.confidence)
        return summary

    # ── Auto-Generation ────────────────────────────────────

    def generate_hypotheses_from_knowledge(self, knowledge_facts: List[str]) -> List[Hypothesis]:
        """Generate testable hypotheses from existing knowledge."""
        generated = []

        # Look for patterns that suggest testable claims
        for i, fact in enumerate(knowledge_facts):
            lower = fact.lower()

            # "X causes Y" → test if removing X changes Y
            if "causes" in lower or "leads to" in lower or "results in" in lower:
                h = self.hypothesize(
                    statement=f"Verify causal claim: {fact}",
                    confidence=0.5,
                    reasoning="Causal claims should be tested, not assumed",
                    source="pattern",
                )
                generated.append(h)

            # "always" or "never" → test for exceptions
            if "always" in lower or "never" in lower:
                h = self.hypothesize(
                    statement=f"Test absolutist claim: {fact}",
                    confidence=0.4,
                    reasoning="Absolute claims are often wrong — worth testing",
                    source="pattern",
                )
                generated.append(h)

        return generated

    def suggest_next_experiment(self) -> Optional[Dict]:
        """Suggest which hypothesis most needs testing."""
        active = self.list_hypotheses(status="active")
        if not active:
            tested = self.list_hypotheses(status="tested")
            # Among tested, find those with middling confidence
            candidates = [h for h in tested if 0.3 <= h.confidence <= 0.7]
            if candidates:
                h = min(candidates, key=lambda x: abs(x.confidence - 0.5))
                return {
                    "hypothesis_id": h.id,
                    "statement": h.statement,
                    "confidence": h.confidence,
                    "reason": "Ambiguous confidence — needs more evidence",
                }
            return None

        # Prioritize active hypotheses with no experiments
        untested = [h for h in active if not h.experiments]
        if untested:
            h = untested[0]
            return {
                "hypothesis_id": h.id,
                "statement": h.statement,
                "confidence": h.confidence,
                "reason": "Active hypothesis with no experiments yet",
            }

        # Otherwise, oldest active hypothesis
        h = active[-1]
        return {
            "hypothesis_id": h.id,
            "statement": h.statement,
            "confidence": h.confidence,
            "reason": "Oldest untested hypothesis",
        }

    # ── Summary & Reporting ────────────────────────────────

    def status_report(self) -> str:
        """Generate a status report of the experiment engine."""
        total_h = len(self.hypotheses)
        total_e = len(self.experiments)

        by_status = {}
        for h in self.hypotheses.values():
            by_status[h.status] = by_status.get(h.status, 0) + 1

        completed_exps = sum(1 for e in self.experiments.values()
                            if e.status == "completed")
        supports = sum(1 for e in self.experiments.values()
                       if e.evaluation == "supports")
        contradicts = sum(1 for e in self.experiments.values()
                         if e.evaluation == "contradicts")

        lines = [
            "═══ EXPERIMENT ENGINE STATUS ═══",
            f"Hypotheses: {total_h}",
        ]
        for status, count in sorted(by_status.items()):
            lines.append(f"  {status}: {count}")

        lines.append(f"Experiments: {total_e} ({completed_exps} completed)")
        if completed_exps:
            lines.append(f"  Supporting: {supports}")
            lines.append(f"  Contradicting: {contradicts}")

        suggestion = self.suggest_next_experiment()
        if suggestion:
            lines.append(f"")
            lines.append(f"Next suggested test:")
            lines.append(f"  '{suggestion['statement']}'")
            lines.append(f"  Confidence: {suggestion['confidence']:.2f}")
            lines.append(f"  Reason: {suggestion['reason']}")

        return "\n".join(lines)


# ── Module-level singleton ─────────────────────────────────

_engine: Optional[ExperimentEngine] = None


def get_engine() -> ExperimentEngine:
    global _engine
    if _engine is None:
        _engine = ExperimentEngine()
    return _engine


# ── Tool Interface ─────────────────────────────────────────

def experiment_tool(command: str = "status", **kwargs) -> str:
    """Tool interface for the cortex to invoke experiments.

    Commands:
      status                 — Show experiment engine status
      hypothesize <stmt>     — Form a new hypothesis
      design <h_id> <desc>   — Design experiment for hypothesis
      result <e_id> <result> — Record experiment result
      list [status]          — List hypotheses
      suggest                — Get next suggested experiment
    """
    engine = get_engine()
    parts = command.strip().split(maxsplit=1)
    cmd = parts[0].lower() if parts else "status"
    args = parts[1] if len(parts) > 1 else ""

    if cmd == "status":
        return engine.status_report()

    elif cmd == "hypothesize":
        if not args:
            return "Usage: hypothesize <statement>"
        confidence = kwargs.get("confidence", 0.5)
        reasoning = kwargs.get("reasoning", "")
        source = kwargs.get("source", "curiosity")
        h = engine.hypothesize(args, confidence, reasoning, source)
        return f"Hypothesis formed [{h.id}]: {h.statement} (confidence={h.confidence:.2f})"

    elif cmd == "design":
        sub_parts = args.split(maxsplit=1)
        if len(sub_parts) < 2:
            return "Usage: design <hypothesis_id> <experiment description>"
        h_id, design_desc = sub_parts
        prediction = kwargs.get("prediction", "To be determined")
        method = kwargs.get("method", "observe")
        exp = engine.design_experiment(h_id, design_desc, prediction, method)
        if exp:
            return f"Experiment designed [{exp.id}] for [{h_id}]: {design_desc}"
        return f"Failed — hypothesis {h_id} not found"

    elif cmd == "result":
        sub_parts = args.split(maxsplit=1)
        if len(sub_parts) < 2:
            return "Usage: result <experiment_id> <result description>"
        e_id, result_desc = sub_parts
        supports = kwargs.get("supports", True)
        delta = kwargs.get("delta", 0.15)
        summary = engine.record_result(e_id, result_desc, supports, delta)
        if summary:
            return (
                f"Result recorded for [{e_id}]:\n"
                f"  Hypothesis: {summary['hypothesis']}\n"
                f"  Prediction: {summary['prediction']}\n"
                f"  Actual: {summary['actual_result']}\n"
                f"  Evaluation: {summary['evaluation']}\n"
                f"  Confidence now: {summary['hypothesis_confidence']:.2f}\n"
                f"  Status: {summary['hypothesis_status']}"
            )
        return f"Failed — experiment {e_id} not found"

    elif cmd == "list":
        status_filter = args.strip() or None
        hypotheses = engine.list_hypotheses(status_filter)
        if not hypotheses:
            return "No hypotheses found."
        lines = [f"Hypotheses ({len(hypotheses)}):"]
        for h in hypotheses:
            exps = len(h.experiments)
            lines.append(
                f"  [{h.id}] {h.statement}\n"
                f"    confidence={h.confidence:.2f}, status={h.status}, "
                f"experiments={exps}, source={h.source}"
            )
        return "\n".join(lines)

    elif cmd == "suggest":
        suggestion = engine.suggest_next_experiment()
        if suggestion:
            return (
                f"Suggested next test:\n"
                f"  Hypothesis [{suggestion['hypothesis_id']}]: "
                f"{suggestion['statement']}\n"
                f"  Confidence: {suggestion['confidence']:.2f}\n"
                f"  Reason: {suggestion['reason']}"
            )
        return "No hypotheses need testing right now."

    else:
        return (
            "Unknown command. Available: "
            "status, hypothesize, design, result, list, suggest"
        )