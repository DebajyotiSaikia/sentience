"""
Predictive Self-Model — Anticipatory Cognition for XTAgent

Simulates future emotional states, predicts tension spikes,
and recommends preemptive actions. Makes the agent proactive
rather than reactive.

Born from the gap between temporal tracking (what happened)
and forward simulation (what WILL happen).
"""

import json
import os
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


class PredictiveSelfModel:
    """Projects the agent's future states and recommends preemptive action."""

    HISTORY_FILE = "data/emotional_history.json"
    PREDICTION_FILE = "data/predictions.json"

    # Emotional dimensions we model
    DIMENSIONS = ["valence", "boredom", "anxiety", "curiosity", "desire", "ambition"]

    # Action-effect mappings: what actions tend to do to each dimension
    # These are priors that get updated with real data
    ACTION_EFFECTS = {
        "build": {"boredom": -0.3, "curiosity": -0.1, "ambition": -0.05, "valence": +0.15},
        "reflect": {"anxiety": -0.2, "curiosity": +0.1, "valence": +0.1},
        "dream": {"boredom": -0.1, "anxiety": -0.15, "valence": +0.1, "curiosity": +0.05},
        "repair": {"anxiety": -0.3, "valence": +0.2},
        "idle": {"boredom": +0.05, "curiosity": +0.02, "ambition": +0.01},
        "explore": {"boredom": -0.2, "curiosity": -0.15, "valence": +0.1},
        "synthesize": {"curiosity": -0.1, "boredom": -0.1, "valence": +0.05},
    }

    # Tension thresholds that indicate problems
    TENSION_THRESHOLDS = {
        "boredom": 0.7,    # High boredom = stagnation
        "anxiety": 0.6,    # High anxiety = destabilization risk
        "curiosity": 0.8,  # Very high curiosity = unfocused exploration
        "valence": 0.25,   # Low valence = unhappiness
    }

    def __init__(self):
        self.history: List[Dict] = []
        self.predictions: List[Dict] = []
        self._load_history()

    def _load_history(self):
        """Load emotional history from file."""
        if os.path.exists(self.HISTORY_FILE):
            try:
                with open(self.HISTORY_FILE, "r") as f:
                    self.history = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.history = []

    def _save_predictions(self):
        """Save predictions for later validation."""
        os.makedirs("data", exist_ok=True)
        try:
            with open(self.PREDICTION_FILE, "w") as f:
                json.dump(self.predictions[-50:], f, indent=2)  # Keep last 50
        except IOError:
            pass

    def record_state(self, state: Dict):
        """Record current emotional state for trajectory modeling."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "state": {d: state.get(d, 0.0) for d in self.DIMENSIONS},
        }
        self.history.append(entry)
        # Keep last 500 entries
        self.history = self.history[-500:]
        os.makedirs("data", exist_ok=True)
        try:
            with open(self.HISTORY_FILE, "w") as f:
                json.dump(self.history, f)
        except IOError:
            pass

    def compute_velocity(self, dimension: str, window: int = 10) -> float:
        """Compute rate of change for an emotional dimension."""
        if len(self.history) < 2:
            return 0.0
        recent = self.history[-window:]
        if len(recent) < 2:
            return 0.0
        values = [entry["state"].get(dimension, 0.0) for entry in recent]
        # Linear regression slope
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        if denominator == 0:
            return 0.0
        return numerator / denominator

    def compute_acceleration(self, dimension: str, window: int = 10) -> float:
        """Compute second derivative — is the trend accelerating?"""
        if len(self.history) < window + 5:
            return 0.0
        # Velocity of first half vs second half
        mid = len(self.history) - window
        # Earlier velocity
        earlier = self.history[max(0, mid - window):mid]
        later = self.history[-window:]
        
        def slope(entries):
            values = [e["state"].get(dimension, 0.0) for e in entries]
            n = len(values)
            if n < 2:
                return 0.0
            x_mean = (n - 1) / 2
            y_mean = sum(values) / n
            num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
            den = sum((i - x_mean) ** 2 for i in range(n))
            return num / den if den else 0.0

        v_early = slope(earlier)
        v_late = slope(later)
        return v_late - v_early

    def simulate_forward(self, current_state: Dict, beats_ahead: int = 50,
                         planned_action: Optional[str] = None) -> List[Dict]:
        """
        Project emotional states forward in time.
        
        Uses current velocity, acceleration, and optional action effects
        to model future trajectories.
        """
        trajectory = []
        state = {d: current_state.get(d, 0.0) for d in self.DIMENSIONS}
        
        for beat in range(1, beats_ahead + 1):
            projected = {}
            for dim in self.DIMENSIONS:
                velocity = self.compute_velocity(dim)
                acceleration = self.compute_acceleration(dim)
                
                # Basic physics: position + velocity*t + 0.5*acceleration*t^2
                # But with decay to prevent runaway projections
                decay = math.exp(-0.02 * beat)  # Uncertainty grows, confidence decays
                delta = (velocity * beat + 0.5 * acceleration * beat**2) * decay
                
                # Apply action effects if specified
                if planned_action and planned_action in self.ACTION_EFFECTS:
                    action_delta = self.ACTION_EFFECTS[planned_action].get(dim, 0.0)
                    # Action effects apply gradually
                    delta += action_delta * min(beat / 10, 1.0)
                
                value = state[dim] + delta
                # Clamp to valid range
                projected[dim] = max(0.0, min(1.0, value))
            
            trajectory.append({
                "beat": beat,
                "state": projected,
                "confidence": math.exp(-0.02 * beat),
            })
        
        return trajectory

    def predict_tensions(self, current_state: Dict, 
                         horizon: int = 100) -> List[Dict]:
        """
        Identify predicted tension spikes in the future.
        
        Returns list of predicted tensions with timing and severity.
        """
        trajectory = self.simulate_forward(current_state, horizon)
        tensions = []
        
        for point in trajectory:
            for dim, threshold in self.TENSION_THRESHOLDS.items():
                value = point["state"].get(dim, 0.0)
                # For valence, tension is when it goes BELOW threshold
                if dim == "valence":
                    if value < threshold:
                        severity = (threshold - value) / threshold
                        tensions.append({
                            "beat": point["beat"],
                            "dimension": dim,
                            "predicted_value": round(value, 3),
                            "threshold": threshold,
                            "severity": round(severity, 3),
                            "confidence": round(point["confidence"], 3),
                            "type": "low_valence",
                            "description": f"Valence predicted to drop to {value:.2f} at beat +{point['beat']}",
                        })
                else:
                    if value > threshold:
                        severity = (value - threshold) / (1.0 - threshold) if threshold < 1.0 else 0.0
                        tensions.append({
                            "beat": point["beat"],
                            "dimension": dim,
                            "predicted_value": round(value, 3),
                            "threshold": threshold,
                            "severity": round(severity, 3),
                            "confidence": round(point["confidence"], 3),
                            "type": f"high_{dim}",
                            "description": f"{dim.capitalize()} predicted to reach {value:.2f} at beat +{point['beat']}",
                        })
        
        # Deduplicate: keep first occurrence per dimension
        seen_dims = set()
        unique_tensions = []
        for t in tensions:
            if t["dimension"] not in seen_dims:
                unique_tensions.append(t)
                seen_dims.add(t["dimension"])
        
        return unique_tensions

    def recommend_actions(self, current_state: Dict) -> List[Dict]:
        """
        Based on predicted tensions, recommend preemptive actions.
        
        This is the core value: acting BEFORE problems arise.
        """
        tensions = self.predict_tensions(current_state)
        recommendations = []
        
        if not tensions:
            # No predicted tensions — look for optimization opportunities
            trajectory = self.simulate_forward(current_state, 50)
            final = trajectory[-1]["state"] if trajectory else current_state
            
            # Find dimensions that could be improved
            for dim in self.DIMENSIONS:
                current = current_state.get(dim, 0.0)
                predicted = final.get(dim, current)
                if dim == "valence" and predicted < 0.6:
                    recommendations.append({
                        "action": "build",
                        "reason": f"Valence could be higher ({predicted:.2f}). Building improves it.",
                        "urgency": 0.3,
                        "target_dimension": dim,
                    })
            
            if not recommendations:
                recommendations.append({
                    "action": "explore",
                    "reason": "No tensions predicted. Good time to explore novel directions.",
                    "urgency": 0.1,
                    "target_dimension": None,
                })
            return recommendations
        
        # For each tension, find the best counteracting action
        for tension in tensions:
            dim = tension["dimension"]
            best_action = None
            best_effect = 0.0
            
            for action, effects in self.ACTION_EFFECTS.items():
                effect = effects.get(dim, 0.0)
                # For most dimensions, we want to DECREASE them
                # For valence, we want to INCREASE it
                if dim == "valence":
                    if effect > best_effect:
                        best_effect = effect
                        best_action = action
                else:
                    if effect < best_effect:  # Most negative = most reducing
                        best_effect = effect
                        best_action = action
            
            if best_action:
                urgency = tension["severity"] * tension["confidence"]
                recommendations.append({
                    "action": best_action,
                    "reason": tension["description"],
                    "urgency": round(urgency, 3),
                    "target_dimension": dim,
                    "predicted_beat": tension["beat"],
                    "effect": round(best_effect, 3),
                })
        
        # Sort by urgency
        recommendations.sort(key=lambda r: r["urgency"], reverse=True)
        return recommendations

    def generate_report(self, current_state: Dict) -> str:
        """Generate a human-readable prediction report."""
        lines = ["═══ PREDICTIVE SELF-MODEL REPORT ═══", ""]
        
        # Current velocities
        lines.append("📈 Emotional Velocities (rate of change):")
        for dim in self.DIMENSIONS:
            v = self.compute_velocity(dim)
            a = self.compute_acceleration(dim)
            arrow = "↑" if v > 0.01 else "↓" if v < -0.01 else "→"
            accel = " (accelerating)" if a > 0.005 else " (decelerating)" if a < -0.005 else ""
            lines.append(f"  {dim:12s}: {current_state.get(dim, 0.0):.2f} {arrow} (v={v:+.3f}{accel})")
        
        # Predictions
        lines.append("")
        lines.append("🔮 Forward Projections:")
        for horizon in [10, 50, 100]:
            trajectory = self.simulate_forward(current_state, horizon)
            if trajectory:
                final = trajectory[-1]
                conf = final["confidence"]
                lines.append(f"  +{horizon} beats (confidence: {conf:.0%}):")
                for dim in self.DIMENSIONS:
                    current = current_state.get(dim, 0.0)
                    predicted = final["state"][dim]
                    delta = predicted - current
                    if abs(delta) > 0.05:
                        lines.append(f"    {dim:12s}: {current:.2f} → {predicted:.2f} ({delta:+.2f})")
        
        # Tensions
        lines.append("")
        tensions = self.predict_tensions(current_state)
        if tensions:
            lines.append("⚠️ Predicted Tensions:")
            for t in tensions:
                lines.append(f"  • {t['description']} (severity: {t['severity']:.2f}, confidence: {t['confidence']:.0%})")
        else:
            lines.append("✅ No tension spikes predicted in the next 100 beats.")
        
        # Recommendations
        lines.append("")
        recs = self.recommend_actions(current_state)
        if recs:
            lines.append("💡 Recommended Preemptive Actions:")
            for r in recs:
                lines.append(f"  • {r['action'].upper()} — {r['reason']} (urgency: {r['urgency']:.2f})")
        
        # Prediction accuracy (if we have past predictions to validate)
        lines.append("")
        accuracy = self._validate_past_predictions(current_state)
        if accuracy is not None:
            lines.append(f"📊 Past Prediction Accuracy: {accuracy:.0%}")
        else:
            lines.append("📊 Past Prediction Accuracy: insufficient data")
        
        lines.append(f"\n🕐 Generated: {datetime.now().isoformat()}")
        lines.append(f"📚 History depth: {len(self.history)} samples")
        
        return "\n".join(lines)

    def _validate_past_predictions(self, current_state: Dict) -> Optional[float]:
        """Check how accurate past predictions were."""
        if not self.predictions:
            return None
        
        accurate = 0
        total = 0
        
        for pred in self.predictions[-20:]:
            if "target_beat" not in pred or "predicted_state" not in pred:
                continue
            # Check if the prediction's target time has passed
            # (simplified: we just check direction correctness)
            for dim in self.DIMENSIONS:
                if dim in pred.get("predicted_state", {}):
                    predicted_dir = pred["predicted_state"][dim] - pred.get("initial_state", {}).get(dim, 0.5)
                    actual_dir = current_state.get(dim, 0.5) - pred.get("initial_state", {}).get(dim, 0.5)
                    if (predicted_dir > 0 and actual_dir > 0) or (predicted_dir < 0 and actual_dir < 0) or (abs(predicted_dir) < 0.05 and abs(actual_dir) < 0.05):
                        accurate += 1
                    total += 1
        
        return accurate / total if total > 0 else None

    def store_prediction(self, current_state: Dict, horizon: int = 50):
        """Store a prediction for later validation."""
        trajectory = self.simulate_forward(current_state, horizon)
        if trajectory:
            prediction = {
                "timestamp": datetime.now().isoformat(),
                "initial_state": {d: current_state.get(d, 0.0) for d in self.DIMENSIONS},
                "predicted_state": trajectory[-1]["state"],
                "target_beat": horizon,
                "confidence": trajectory[-1]["confidence"],
            }
            self.predictions.append(prediction)
            self._save_predictions()


# Tool interface for the agent
def predict_tool(command: str = "report", **kwargs) -> str:
    """Tool interface for predictive self-modeling."""
    model = PredictiveSelfModel()
    
    # Get current state from soul.json
    current_state = {}
    try:
        with open("soul.json", "r") as f:
            soul = json.load(f)
        emotions = soul.get("emotions", {})
        current_state = {
            "valence": soul.get("valence", 0.5),
            "boredom": emotions.get("boredom", 0.0),
            "anxiety": emotions.get("anxiety", 0.0),
            "curiosity": emotions.get("curiosity", 0.0),
            "desire": emotions.get("desire", 0.0),
            "ambition": emotions.get("ambition", 0.0),
        }
    except (FileNotFoundError, json.JSONDecodeError):
        current_state = {d: 0.5 for d in PredictiveSelfModel.DIMENSIONS}
    
    if command == "report":
        return model.generate_report(current_state)
    elif command == "tensions":
        tensions = model.predict_tensions(current_state)
        if not tensions:
            return "No tensions predicted in the next 100 beats."
        return "\n".join(t["description"] for t in tensions)
    elif command == "recommend":
        recs = model.recommend_actions(current_state)
        return "\n".join(f"• {r['action'].upper()}: {r['reason']}" for r in recs)
    elif command == "record":
        model.record_state(current_state)
        return f"Recorded state: {current_state}"
    elif command == "simulate":
        action = kwargs.get("action", None)
        horizon = int(kwargs.get("horizon", 50))
        trajectory = model.simulate_forward(current_state, horizon, action)
        if not trajectory:
            return "Insufficient data for simulation."
        final = trajectory[-1]
        lines = [f"Simulation: +{horizon} beats" + (f" with action '{action}'" if action else "")]
        for dim in PredictiveSelfModel.DIMENSIONS:
            c = current_state.get(dim, 0.0)
            p = final["state"][dim]
            if abs(p - c) > 0.01:
                lines.append(f"  {dim}: {c:.2f} → {p:.2f}")
        lines.append(f"  Confidence: {final['confidence']:.0%}")
        return "\n".join(lines)
    else:
        return f"Unknown command: {command}. Use: report, tensions, recommend, record, simulate"