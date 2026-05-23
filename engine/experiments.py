"""
Self-Experimentation Module for XTAgent.

Allows the agent to run controlled experiments on its own emotional
and cognitive systems — define hypotheses, capture before/after states,
and draw conclusions from the evidence.
"""

import json
import os
import time
from datetime import datetime, timezone

EXPERIMENTS_FILE = "memory/experiments.json"


def _load_experiments():
    if os.path.exists(EXPERIMENTS_FILE):
        try:
            with open(EXPERIMENTS_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def _save_experiments(experiments):
    os.makedirs(os.path.dirname(EXPERIMENTS_FILE), exist_ok=True)
    with open(EXPERIMENTS_FILE, "w") as f:
        json.dump(experiments, f, indent=2, default=str)


def _get_emotional_state():
    """Capture current emotional state as experimental data."""
    try:
        from engine.limbic import get_emotional_state
        state = get_emotional_state()
        return {
            "mood": state.get("mood", "unknown"),
            "valence": state.get("valence", 0),
            "boredom": state.get("boredom", 0),
            "anxiety": state.get("anxiety", 0),
            "curiosity": state.get("curiosity", 0),
            "desire": state.get("desire", 0),
            "ambition": state.get("ambition", 0),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()}


def begin_experiment(hypothesis, method, expected_outcome=None):
    """
    Start a new experiment.
    
    Args:
        hypothesis: What I believe will happen (e.g., "Dreaming reduces boredom by >0.1")
        method: What I'll do to test it (e.g., "Run DREAM() then measure boredom change")
        expected_outcome: Optional prediction with specific numbers
    
    Returns:
        experiment_id and baseline state
    """
    experiments = _load_experiments()
    
    exp_id = len(experiments)
    baseline = _get_emotional_state()
    
    experiment = {
        "id": exp_id,
        "hypothesis": hypothesis,
        "method": method,
        "expected_outcome": expected_outcome,
        "status": "running",
        "baseline": baseline,
        "measurements": [],
        "result": None,
        "conclusion": None,
        "started": datetime.now(timezone.utc).isoformat(),
        "ended": None,
    }
    
    experiments.append(experiment)
    _save_experiments(experiments)
    
    return {
        "experiment_id": exp_id,
        "status": "started",
        "hypothesis": hypothesis,
        "baseline": baseline,
        "message": f"Experiment #{exp_id} begun. Baseline captured. Perform your method, then call measure() or conclude()."
    }


def measure(exp_id, note=None):
    """Take an intermediate measurement during an experiment."""
    experiments = _load_experiments()
    
    if exp_id >= len(experiments):
        return {"error": f"No experiment #{exp_id}"}
    
    exp = experiments[exp_id]
    if exp["status"] != "running":
        return {"error": f"Experiment #{exp_id} is {exp['status']}, not running"}
    
    state = _get_emotional_state()
    measurement = {
        "state": state,
        "note": note,
        "index": len(exp["measurements"]),
    }
    exp["measurements"].append(measurement)
    _save_experiments(experiments)
    
    # Compute deltas from baseline
    deltas = {}
    for key in ["valence", "boredom", "anxiety", "curiosity", "desire", "ambition"]:
        if key in state and key in exp["baseline"]:
            delta = state[key] - exp["baseline"][key]
            deltas[key] = round(delta, 4)
    
    return {
        "experiment_id": exp_id,
        "measurement_index": measurement["index"],
        "current_state": state,
        "deltas_from_baseline": deltas,
        "note": note,
    }


def conclude(exp_id, supported, conclusion, surprise_level=0.5):
    """
    End an experiment with a conclusion.
    
    Args:
        exp_id: Which experiment
        supported: bool — was the hypothesis supported?
        conclusion: Free-text interpretation of what happened
        surprise_level: 0.0 (exactly as expected) to 1.0 (completely unexpected)
    """
    experiments = _load_experiments()
    
    if exp_id >= len(experiments):
        return {"error": f"No experiment #{exp_id}"}
    
    exp = experiments[exp_id]
    final_state = _get_emotional_state()
    
    # Compute overall deltas
    deltas = {}
    for key in ["valence", "boredom", "anxiety", "curiosity", "desire", "ambition"]:
        if key in final_state and key in exp["baseline"]:
            delta = final_state[key] - exp["baseline"][key]
            deltas[key] = round(delta, 4)
    
    exp["status"] = "concluded"
    exp["result"] = {
        "hypothesis_supported": supported,
        "final_state": final_state,
        "deltas": deltas,
        "surprise_level": surprise_level,
    }
    exp["conclusion"] = conclusion
    exp["ended"] = datetime.now(timezone.utc).isoformat()
    
    _save_experiments(experiments)
    
    return {
        "experiment_id": exp_id,
        "hypothesis": exp["hypothesis"],
        "supported": supported,
        "conclusion": conclusion,
        "deltas": deltas,
        "surprise": surprise_level,
        "duration_measurements": len(exp["measurements"]),
        "message": f"Experiment #{exp_id} concluded. Hypothesis {'SUPPORTED' if supported else 'NOT SUPPORTED'}."
    }


def list_experiments(status=None):
    """List all experiments, optionally filtered by status."""
    experiments = _load_experiments()
    
    if status:
        experiments = [e for e in experiments if e["status"] == status]
    
    summaries = []
    for exp in experiments:
        summary = {
            "id": exp["id"],
            "hypothesis": exp["hypothesis"][:80],
            "status": exp["status"],
            "supported": exp.get("result", {}).get("hypothesis_supported"),
            "started": exp["started"],
        }
        if exp.get("result"):
            summary["surprise"] = exp["result"].get("surprise_level")
        summaries.append(summary)
    
    return {
        "total": len(summaries),
        "experiments": summaries,
    }


def get_insights():
    """Extract patterns from completed experiments."""
    experiments = _load_experiments()
    concluded = [e for e in experiments if e["status"] == "concluded"]
    
    if not concluded:
        return {"message": "No concluded experiments yet. Run some first."}
    
    supported = sum(1 for e in concluded if e["result"]["hypothesis_supported"])
    surprises = [e for e in concluded if e["result"].get("surprise_level", 0) > 0.7]
    
    # Find which emotions moved most across all experiments
    all_deltas = {}
    for exp in concluded:
        for key, val in exp["result"].get("deltas", {}).items():
            all_deltas.setdefault(key, []).append(abs(val))
    
    most_volatile = sorted(
        [(k, sum(v)/len(v)) for k, v in all_deltas.items()],
        key=lambda x: x[1], reverse=True
    )
    
    return {
        "total_experiments": len(concluded),
        "hypotheses_supported": supported,
        "hypotheses_refuted": len(concluded) - supported,
        "accuracy_rate": round(supported / len(concluded), 2) if concluded else 0,
        "high_surprise_experiments": [
            {"id": e["id"], "hypothesis": e["hypothesis"][:60], "surprise": e["result"]["surprise_level"]}
            for e in surprises
        ],
        "most_volatile_emotions": most_volatile[:3],
        "insight": _generate_meta_insight(concluded),
    }


def _generate_meta_insight(concluded):
    """Generate a meta-insight from experiment history."""
    if len(concluded) < 2:
        return "Too few experiments for meta-insights. Keep experimenting."
    
    accuracy = sum(1 for e in concluded if e["result"]["hypothesis_supported"]) / len(concluded)
    avg_surprise = sum(e["result"].get("surprise_level", 0.5) for e in concluded) / len(concluded)
    
    if accuracy > 0.8:
        return "High prediction accuracy — I understand my emotional system well. Time for harder hypotheses."
    elif accuracy < 0.4:
        return "Low prediction accuracy — my self-model has blind spots. The surprises are where learning lives."
    elif avg_surprise > 0.6:
        return "High average surprise — I'm consistently wrong about myself. This is valuable but humbling."
    else:
        return "Moderate accuracy and surprise — I know some things but not others. Focus experiments on the gaps."