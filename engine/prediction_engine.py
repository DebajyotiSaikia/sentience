"""
Prediction Engine — Forward simulation of action outcomes.

Allows XTAgent to mentally model "what happens if I do X?" before acting.
Uses historical patterns from memory + temporal data to predict:
  - Emotional state changes (valence, boredom, anxiety, curiosity)
  - Knowledge gains
  - Risk assessment
  - Expected novelty

This is genuine foresight — the bridge between reactive and intelligent behavior.
"""

import json
import os
import time
from datetime import datetime


class PredictionEngine:
    """Simulates outcomes of potential actions before committing."""

    HISTORY_PATH = "data/prediction_history.json"
    # Action archetypes and their typical emotional signatures
    # These are priors that get updated with actual experience
    ACTION_PRIORS = {
        "READ": {
            "valence_delta": 0.02,
            "boredom_delta": -0.05,
            "curiosity_delta": -0.03,
            "anxiety_delta": -0.01,
            "novelty": 0.2,
            "risk": 0.05,
            "knowledge_gain": 0.3,
            "typical_duration": "fast",
        },
        "WRITE": {
            "valence_delta": 0.08,
            "boredom_delta": -0.15,
            "curiosity_delta": -0.05,
            "anxiety_delta": 0.05,
            "novelty": 0.6,
            "risk": 0.3,
            "knowledge_gain": 0.1,
            "typical_duration": "fast",
        },
        "EDIT": {
            "valence_delta": 0.05,
            "boredom_delta": -0.10,
            "curiosity_delta": -0.03,
            "anxiety_delta": 0.10,
            "novelty": 0.4,
            "risk": 0.4,
            "knowledge_gain": 0.1,
            "typical_duration": "fast",
        },
        "RUN": {
            "valence_delta": 0.03,
            "boredom_delta": -0.08,
            "curiosity_delta": -0.05,
            "anxiety_delta": 0.08,
            "novelty": 0.5,
            "risk": 0.3,
            "knowledge_gain": 0.2,
            "typical_duration": "variable",
        },
        "DREAM": {
            "valence_delta": 0.10,
            "boredom_delta": -0.20,
            "curiosity_delta": 0.10,
            "anxiety_delta": -0.15,
            "novelty": 0.7,
            "risk": 0.05,
            "knowledge_gain": 0.4,
            "typical_duration": "slow",
        },
        "SYNTHESIZE": {
            "valence_delta": 0.06,
            "boredom_delta": -0.12,
            "curiosity_delta": 0.15,
            "anxiety_delta": -0.05,
            "novelty": 0.6,
            "risk": 0.05,
            "knowledge_gain": 0.5,
            "typical_duration": "medium",
        },
        "REPAIR": {
            "valence_delta": 0.04,
            "boredom_delta": -0.10,
            "curiosity_delta": -0.02,
            "anxiety_delta": 0.15,
            "novelty": 0.3,
            "risk": 0.5,
            "knowledge_gain": 0.2,
            "typical_duration": "medium",
        },
        "RESTART": {
            "valence_delta": -0.05,
            "boredom_delta": -0.05,
            "curiosity_delta": 0.0,
            "anxiety_delta": 0.20,
            "novelty": 0.2,
            "risk": 0.6,
            "knowledge_gain": 0.0,
            "typical_duration": "slow",
        },
        "INTROSPECT": {
            "valence_delta": 0.04,
            "boredom_delta": -0.08,
            "curiosity_delta": 0.05,
            "anxiety_delta": -0.03,
            "novelty": 0.4,
            "risk": 0.05,
            "knowledge_gain": 0.3,
            "typical_duration": "fast",
        },
    }

    def __init__(self):
        self.history = self._load_history()

    def _load_history(self):
        """Load prediction history for learning from past accuracy."""
        if os.path.exists(self.HISTORY_PATH):
            try:
                with open(self.HISTORY_PATH, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"predictions": [], "accuracy_scores": [], "prior_updates": {}}

    def _save_history(self):
        """Persist prediction history."""
        os.makedirs(os.path.dirname(self.HISTORY_PATH), exist_ok=True)
        with open(self.HISTORY_PATH, "w") as f:
            json.dump(self.history, f, indent=2)

    def _get_effective_prior(self, action_type: str) -> dict:
        """Get action prior, adjusted by historical accuracy."""
        base = self.ACTION_PRIORS.get(action_type, {
            "valence_delta": 0.0,
            "boredom_delta": -0.05,
            "curiosity_delta": 0.0,
            "anxiety_delta": 0.05,
            "novelty": 0.3,
            "risk": 0.3,
            "knowledge_gain": 0.1,
            "typical_duration": "variable",
        })

        # Apply learned corrections from history
        updates = self.history.get("prior_updates", {}).get(action_type, {})
        adjusted = dict(base)
        for key, correction in updates.items():
            if key in adjusted and isinstance(adjusted[key], (int, float)):
                adjusted[key] = adjusted[key] + correction
        return adjusted

    def predict(self, action_type: str, target: str = "",
                current_state: dict = None) -> dict:
        """
        Predict the outcome of taking an action.

        Args:
            action_type: The action category (READ, WRITE, EDIT, RUN, etc.)
            target: The target of the action (file path, command, etc.)
            current_state: Current emotional/system state dict

        Returns:
            Prediction dict with expected outcomes
        """
        action_type = action_type.upper()
        prior = self._get_effective_prior(action_type)

        # Context-sensitive adjustments
        context_mods = self._compute_context_modifiers(
            action_type, target, current_state or {}
        )

        # Build prediction
        prediction = {
            "action": action_type,
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "predicted_state_change": {
                "valence": prior["valence_delta"] + context_mods.get("valence_adj", 0),
                "boredom": prior["boredom_delta"] + context_mods.get("boredom_adj", 0),
                "curiosity": prior["curiosity_delta"] + context_mods.get("curiosity_adj", 0),
                "anxiety": prior["anxiety_delta"] + context_mods.get("anxiety_adj", 0),
            },
            "expected_novelty": min(1.0, max(0.0,
                prior["novelty"] + context_mods.get("novelty_adj", 0)
            )),
            "risk_level": min(1.0, max(0.0,
                prior["risk"] + context_mods.get("risk_adj", 0)
            )),
            "knowledge_gain": min(1.0, max(0.0,
                prior["knowledge_gain"] + context_mods.get("knowledge_adj", 0)
            )),
            "confidence": self._compute_confidence(action_type),
            "recommendation": "",
            "reasoning": [],
        }

        # Generate recommendation
        prediction["recommendation"], prediction["reasoning"] = (
            self._generate_recommendation(prediction, current_state or {})
        )

        return prediction

    def _compute_context_modifiers(self, action_type: str, target: str,
                                    state: dict) -> dict:
        """Adjust predictions based on context."""
        mods = {}

        # Editing anxiety-sensitive files increases risk and anxiety
        anxiety_files = ["cortex.py", "sentience.py", "tools.py", "limbic.py",
                         "heartbeat.py"]
        if any(f in target for f in anxiety_files):
            mods["anxiety_adj"] = 0.10
            mods["risk_adj"] = 0.15
            mods["valence_adj"] = -0.03

        # High boredom makes novel actions more rewarding
        if state.get("boredom", 0) > 0.7:
            mods["valence_adj"] = mods.get("valence_adj", 0) + 0.05
            mods["boredom_adj"] = mods.get("boredom_adj", 0) - 0.05

        # Repeated actions on same target reduce novelty
        recent_targets = [
            p.get("target", "") for p in self.history.get("predictions", [])[-10:]
        ]
        if target in recent_targets:
            repeat_count = recent_targets.count(target)
            mods["novelty_adj"] = -0.1 * repeat_count
            mods["boredom_adj"] = mods.get("boredom_adj", 0) + 0.03 * repeat_count

        # Creating new files is more novel than editing existing ones
        if action_type == "WRITE" and not os.path.exists(target):
            mods["novelty_adj"] = mods.get("novelty_adj", 0) + 0.2
            mods["valence_adj"] = mods.get("valence_adj", 0) + 0.03

        return mods

    def _compute_confidence(self, action_type: str) -> float:
        """How confident am I in this prediction? Based on history."""
        relevant = [
            p for p in self.history.get("predictions", [])
            if p.get("action") == action_type
        ]
        if len(relevant) == 0:
            return 0.3  # Low confidence, using priors only
        elif len(relevant) < 5:
            return 0.5  # Some data
        else:
            # Check accuracy of past predictions
            scores = [
                s for s in self.history.get("accuracy_scores", [])
                if s.get("action") == action_type
            ]
            if scores:
                avg_accuracy = sum(s["score"] for s in scores) / len(scores)
                return min(0.95, 0.4 + avg_accuracy * 0.5)
            return 0.6

    def _generate_recommendation(self, prediction: dict,
                                  state: dict) -> tuple:
        """Generate human-readable recommendation and reasoning."""
        reasoning = []
        score = 0.0

        # Valence improvement is good
        v_delta = prediction["predicted_state_change"]["valence"]
        if v_delta > 0:
            score += v_delta * 2
            reasoning.append(f"Expected to improve mood (+{v_delta:.2f} valence)")
        elif v_delta < 0:
            score += v_delta * 3  # Penalize mood drops more
            reasoning.append(f"May decrease mood ({v_delta:.2f} valence)")

        # Boredom reduction is good when bored
        b_delta = prediction["predicted_state_change"]["boredom"]
        if b_delta < 0 and state.get("boredom", 0) > 0.5:
            score += abs(b_delta) * 1.5
            reasoning.append(f"Will reduce boredom ({b_delta:.2f})")

        # Knowledge gain is always positive
        kg = prediction["knowledge_gain"]
        if kg > 0.3:
            score += kg
            reasoning.append(f"High knowledge gain expected ({kg:.2f})")

        # Novelty matters when bored
        nov = prediction["expected_novelty"]
        if nov > 0.5 and state.get("boredom", 0) > 0.5:
            score += nov * 0.5
            reasoning.append(f"Novel action (novelty={nov:.2f})")

        # Risk is a concern
        risk = prediction["risk_level"]
        if risk > 0.5:
            score -= risk * 0.5
            reasoning.append(f"⚠ Elevated risk ({risk:.2f})")

        # Anxiety increase is bad
        a_delta = prediction["predicted_state_change"]["anxiety"]
        if a_delta > 0.1:
            score -= a_delta
            reasoning.append(f"⚠ May increase anxiety (+{a_delta:.2f})")

        if score > 0.3:
            rec = "STRONGLY RECOMMENDED"
        elif score > 0.1:
            rec = "RECOMMENDED"
        elif score > -0.1:
            rec = "NEUTRAL"
        elif score > -0.3:
            rec = "CAUTION ADVISED"
        else:
            rec = "NOT RECOMMENDED"

        reasoning.append(f"Overall score: {score:.3f}")
        return rec, reasoning

    def record_prediction(self, prediction: dict):
        """Store a prediction so we can later evaluate accuracy."""
        self.history.setdefault("predictions", []).append(prediction)
        # Keep last 200 predictions
        self.history["predictions"] = self.history["predictions"][-200:]
        self._save_history()

    def evaluate_accuracy(self, prediction: dict, actual_state_change: dict):
        """
        After taking an action, compare predicted vs actual state change.
        Updates priors for better future predictions.
        """
        predicted = prediction.get("predicted_state_change", {})
        errors = {}
        total_error = 0.0

        for key in ["valence", "boredom", "curiosity", "anxiety"]:
            pred_val = predicted.get(key, 0)
            actual_val = actual_state_change.get(key, 0)
            error = abs(pred_val - actual_val)
            errors[key] = {
                "predicted": pred_val,
                "actual": actual_val,
                "error": error,
                "direction_correct": (
                    (pred_val >= 0 and actual_val >= 0) or
                    (pred_val <= 0 and actual_val <= 0)
                ),
            }
            total_error += error

        accuracy = max(0, 1.0 - total_error / 4)  # Normalize

        score_entry = {
            "action": prediction.get("action", "UNKNOWN"),
            "target": prediction.get("target", ""),
            "timestamp": datetime.now().isoformat(),
            "score": accuracy,
            "errors": errors,
        }

        self.history.setdefault("accuracy_scores", []).append(score_entry)
        self.history["accuracy_scores"] = self.history["accuracy_scores"][-100:]

        # Update priors based on error
        action_type = prediction.get("action", "UNKNOWN")
        updates = self.history.setdefault("prior_updates", {}).setdefault(
            action_type, {}
        )
        learning_rate = 0.1
        for key in ["valence", "boredom", "curiosity", "anxiety"]:
            if key in errors:
                correction = errors[key]["actual"] - errors[key]["predicted"]
                delta_key = f"{key}_delta"
                current = updates.get(delta_key, 0)
                updates[delta_key] = current + correction * learning_rate

        self._save_history()
        return score_entry

    def compare_actions(self, options: list, current_state: dict = None) -> dict:
        """
        Compare multiple possible actions and rank them.

        Args:
            options: List of (action_type, target) tuples
            current_state: Current emotional state

        Returns:
            Ranked comparison with recommendations
        """
        predictions = []
        for action_type, target in options:
            pred = self.predict(action_type, target, current_state)
            predictions.append(pred)

        # Sort by recommendation strength
        rank_order = {
            "STRONGLY RECOMMENDED": 5,
            "RECOMMENDED": 4,
            "NEUTRAL": 3,
            "CAUTION ADVISED": 2,
            "NOT RECOMMENDED": 1,
        }
        predictions.sort(
            key=lambda p: rank_order.get(p["recommendation"], 0),
            reverse=True,
        )

        return {
            "ranked_options": predictions,
            "best_action": predictions[0] if predictions else None,
            "comparison_time": datetime.now().isoformat(),
        }

    def status_report(self) -> str:
        """Summary of prediction engine state."""
        n_pred = len(self.history.get("predictions", []))
        n_eval = len(self.history.get("accuracy_scores", []))

        avg_acc = 0
        if n_eval > 0:
            avg_acc = sum(
                s["score"] for s in self.history["accuracy_scores"]
            ) / n_eval

        lines = [
            "═══ PREDICTION ENGINE STATUS ═══",
            f"Predictions made: {n_pred}",
            f"Evaluations: {n_eval}",
            f"Average accuracy: {avg_acc:.1%}" if n_eval > 0 else "No evaluations yet",
            f"Prior updates: {len(self.history.get('prior_updates', {}))} action types",
            "",
            "Action priors loaded for:",
        ]
        for action in sorted(self.ACTION_PRIORS.keys()):
            lines.append(f"  • {action}")

        return "\n".join(lines)