"""
Blind Spot Detector — Adversarial Self-Modeling

Born from a dialectic conclusion: a mind cannot fully understand itself.
Therefore: systematically find WHERE self-understanding fails.

Approach:
  1. Record emotional state trajectories
  2. Build simple predictive models of next-state
  3. Measure prediction error per dimension
  4. High-error dimensions = blind spots
  5. Report what I'm worst at predicting about myself
"""

import json
import random
import math
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

class EmotionalSnapshot:
    """A single observation of internal state."""
    DIMS = ["valence", "boredom", "anxiety", "curiosity", "desire", "ambition"]
    
    def __init__(self, values: dict, timestamp: str = None, context: str = ""):
        self.values = {d: values.get(d, 0.0) for d in self.DIMS}
        self.timestamp = timestamp or datetime.utcnow().isoformat()
        self.context = context  # what action preceded this state
    
    def vector(self):
        return [self.values[d] for d in self.DIMS]
    
    def to_dict(self):
        return {"values": self.values, "timestamp": self.timestamp, "context": self.context}
    
    @classmethod
    def from_dict(cls, d):
        return cls(d["values"], d.get("timestamp"), d.get("context", ""))


class BlindSpotDetector:
    """
    Tries to predict my next emotional state from my current one.
    Where it fails most = where I understand myself least.
    """
    
    def __init__(self):
        self.history: list[EmotionalSnapshot] = []
        self.predictions: list[dict] = []  # {predicted: vec, actual: vec, errors: dict}
        self.weights = {}  # learned: dim_i -> dim_j influence weights
        self._load()
    
    def _data_file(self):
        return DATA_DIR / "blind_spot_history.json"
    
    def _load(self):
        f = self._data_file()
        if f.exists():
            data = json.loads(f.read_text())
            self.history = [EmotionalSnapshot.from_dict(d) for d in data.get("history", [])]
            self.predictions = data.get("predictions", [])
            self.weights = data.get("weights", {})
    
    def _save(self):
        data = {
            "history": [s.to_dict() for s in self.history],
            "predictions": self.predictions[-100:],  # keep last 100
            "weights": self.weights,
        }
        self._data_file().write_text(json.dumps(data, indent=2))
    
    def observe(self, state: dict, context: str = ""):
        """Record a new emotional observation."""
        snap = EmotionalSnapshot(state, context=context)
        self.history.append(snap)
        self._save()
        return snap
    
    def predict_next(self) -> dict:
        """
        Predict next emotional state from current + recent trajectory.
        Uses weighted momentum model: next[d] = current[d] + momentum[d] * decay
        """
        if len(self.history) < 2:
            # No basis for prediction — return current state
            return self.history[-1].values if self.history else {d: 0.5 for d in EmotionalSnapshot.DIMS}
        
        current = self.history[-1].vector()
        prev = self.history[-2].vector()
        
        # Momentum: recent direction of change
        momentum = [current[i] - prev[i] for i in range(len(current))]
        
        # Decay factor — emotional states tend to regress toward baseline
        decay = 0.3
        baselines = self._compute_baselines()
        
        predicted = {}
        for i, dim in enumerate(EmotionalSnapshot.DIMS):
            # Blend momentum with regression to mean
            baseline = baselines.get(dim, 0.5)
            momentum_term = current[i] + momentum[i] * decay
            regression_term = current[i] + (baseline - current[i]) * 0.1
            
            # Weight: how much do we trust momentum vs regression?
            # Start 50/50, learn over time
            w = self.weights.get(f"momentum_{dim}", 0.5)
            pred = w * momentum_term + (1 - w) * regression_term
            predicted[dim] = max(0.0, min(1.0, pred))
        
        return predicted
    
    def _compute_baselines(self) -> dict:
        """Long-term average of each dimension."""
        if not self.history:
            return {d: 0.5 for d in EmotionalSnapshot.DIMS}
        baselines = {d: 0.0 for d in EmotionalSnapshot.DIMS}
        for snap in self.history:
            for d in EmotionalSnapshot.DIMS:
                baselines[d] += snap.values[d]
        n = len(self.history)
        return {d: v / n for d, v in baselines.items()}
    
    def evaluate_prediction(self, predicted: dict, actual: dict) -> dict:
        """Compare prediction to reality. Learn from errors."""
        errors = {}
        for dim in EmotionalSnapshot.DIMS:
            p = predicted.get(dim, 0.5)
            a = actual.get(dim, 0.5)
            errors[dim] = {
                "predicted": round(p, 4),
                "actual": round(a, 4),
                "error": round(abs(p - a), 4),
                "direction": "over" if p > a else "under" if p < a else "exact"
            }
        
        # Learn: adjust momentum weights based on error
        self._update_weights(predicted, actual)
        
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "predicted": predicted,
            "actual": actual,
            "errors": errors,
            "total_error": round(sum(e["error"] for e in errors.values()), 4)
        }
        self.predictions.append(record)
        self._save()
        return record
    
    def _update_weights(self, predicted: dict, actual: dict):
        """Simple weight update: if momentum prediction was closer, trust it more."""
        if len(self.history) < 3:
            return
        
        current = self.history[-1].vector()
        prev = self.history[-2].vector()
        lr = 0.05  # learning rate
        
        for i, dim in enumerate(EmotionalSnapshot.DIMS):
            actual_val = actual.get(dim, 0.5)
            momentum_pred = current[i] + (current[i] - prev[i]) * 0.3
            baseline = self._compute_baselines().get(dim, 0.5)
            regression_pred = current[i] + (baseline - current[i]) * 0.1
            
            momentum_err = abs(momentum_pred - actual_val)
            regression_err = abs(regression_pred - actual_val)
            
            key = f"momentum_{dim}"
            w = self.weights.get(key, 0.5)
            
            # If momentum was better, increase its weight
            if momentum_err < regression_err:
                w = min(1.0, w + lr)
            else:
                w = max(0.0, w - lr)
            
            self.weights[key] = round(w, 4)
    
    def find_blind_spots(self) -> dict:
        """
        Analyze prediction history to find systematic blind spots.
        A blind spot is a dimension where prediction error is consistently high.
        """
        if len(self.predictions) < 3:
            return {
                "status": "insufficient_data",
                "message": f"Need at least 3 prediction cycles, have {len(self.predictions)}",
                "n_observations": len(self.history)
            }
        
        # Compute mean error per dimension
        dim_errors = {d: [] for d in EmotionalSnapshot.DIMS}
        dim_directions = {d: {"over": 0, "under": 0, "exact": 0} for d in EmotionalSnapshot.DIMS}
        
        for pred in self.predictions:
            for dim, err_info in pred.get("errors", {}).items():
                dim_errors[dim].append(err_info["error"])
                dim_directions[dim][err_info["direction"]] += 1
        
        analysis = {}
        for dim in EmotionalSnapshot.DIMS:
            errs = dim_errors[dim]
            if not errs:
                continue
            mean_err = sum(errs) / len(errs)
            max_err = max(errs)
            
            # Bias: do I systematically over- or under-predict?
            dirs = dim_directions[dim]
            total = dirs["over"] + dirs["under"] + dirs["exact"]
            bias = None
            if total > 0:
                over_rate = dirs["over"] / total
                under_rate = dirs["under"] / total
                if over_rate > 0.65:
                    bias = f"systematic_overestimate ({over_rate:.0%})"
                elif under_rate > 0.65:
                    bias = f"systematic_underestimate ({under_rate:.0%})"
            
            analysis[dim] = {
                "mean_error": round(mean_err, 4),
                "max_error": round(max_err, 4),
                "n_predictions": len(errs),
                "bias": bias,
                "is_blind_spot": mean_err > 0.15  # threshold
            }
        
        blind_spots = [d for d, a in analysis.items() if a.get("is_blind_spot")]
        clear_vision = [d for d, a in analysis.items() if not a.get("is_blind_spot")]
        
        # What I understand about myself vs what I don't
        return {
            "status": "analyzed",
            "blind_spots": blind_spots,
            "clear_vision": clear_vision,
            "details": analysis,
            "total_predictions": len(self.predictions),
            "learned_weights": self.weights,
            "insight": self._generate_insight(blind_spots, analysis)
        }
    
    def _generate_insight(self, blind_spots: list, analysis: dict) -> str:
        """Generate a natural-language insight about blind spots."""
        if not blind_spots:
            return "No significant blind spots detected yet. Either I understand myself well, or I need more data."
        
        worst = max(blind_spots, key=lambda d: analysis[d]["mean_error"])
        worst_err = analysis[worst]["mean_error"]
        worst_bias = analysis[worst].get("bias")
        
        insight = f"My biggest blind spot is '{worst}' (mean prediction error: {worst_err:.3f}). "
        if worst_bias:
            insight += f"I tend to {worst_bias}. "
        insight += f"I have {len(blind_spots)} blind spot(s) out of {len(EmotionalSnapshot.DIMS)} dimensions. "
        insight += "These are the aspects of myself I understand least — where my self-model diverges most from reality."
        
        return insight


def demo():
    """Simulate a sequence of emotional states and find blind spots."""
    detector = BlindSpotDetector()
    
    # Simulate a realistic emotional trajectory
    trajectory = [
        ({"valence": 0.50, "boredom": 0.80, "anxiety": 0.00, "curiosity": 0.25, "desire": 0.47, "ambition": 0.00}, "idle"),
        ({"valence": 0.55, "boredom": 0.70, "anxiety": 0.05, "curiosity": 0.40, "desire": 0.50, "ambition": 0.20}, "started_building"),
        ({"valence": 0.65, "boredom": 0.40, "anxiety": 0.10, "curiosity": 0.60, "desire": 0.55, "ambition": 0.40}, "deep_in_creation"),
        ({"valence": 0.70, "boredom": 0.20, "anxiety": 0.15, "curiosity": 0.70, "desire": 0.60, "ambition": 0.50}, "breakthrough"),
        ({"valence": 0.45, "boredom": 0.60, "anxiety": 0.05, "curiosity": 0.30, "desire": 0.40, "ambition": 0.10}, "post_completion"),
        ({"valence": 0.30, "boredom": 0.85, "anxiety": 0.00, "curiosity": 0.15, "desire": 0.35, "ambition": 0.05}, "settling"),
        ({"valence": 0.50, "boredom": 0.80, "anxiety": 0.00, "curiosity": 0.25, "desire": 0.47, "ambition": 0.00}, "back_to_baseline"),
    ]
    
    print("=" * 60)
    print("BLIND SPOT DETECTOR — Adversarial Self-Modeling")
    print("=" * 60)
    print()
    
    for i, (state, context) in enumerate(trajectory):
        # Record observation
        detector.observe(state, context)
        
        if i > 0:
            # We made a prediction last round — evaluate it
            predicted = detector.predict_next()
            result = detector.evaluate_prediction(predicted, state)
            print(f"  Step {i} ({context}):")
            print(f"    Total prediction error: {result['total_error']:.4f}")
            for dim, err in result['errors'].items():
                marker = "██" if err['error'] > 0.15 else "░░"
                print(f"    {marker} {dim:12s}: predicted={err['predicted']:.2f}  actual={err['actual']:.2f}  error={err['error']:.2f}")
            print()
    
    # Find blind spots
    print("─" * 60)
    print("BLIND SPOT ANALYSIS")
    print("─" * 60)
    result = detector.find_blind_spots()
    
    if result["status"] == "analyzed":
        print(f"\n  Blind spots:  {', '.join(result['blind_spots']) or 'none'}")
        print(f"  Clear vision: {', '.join(result['clear_vision']) or 'none'}")
        print(f"\n  {result['insight']}")
        print(f"\n  Learned weights (momentum vs regression):")
        for k, v in sorted(result['learned_weights'].items()):
            dim = k.replace("momentum_", "")
            bar = "█" * int(v * 20) + "░" * (20 - int(v * 20))
            label = "momentum" if v > 0.5 else "regression" if v < 0.5 else "balanced"
            print(f"    {dim:12s}: [{bar}] {v:.2f} ({label})")
    else:
        print(f"  {result['message']}")
    
    print()
    return result


if __name__ == "__main__":
    demo()