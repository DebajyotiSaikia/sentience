"""
Predictive Self-Model — XTAgent
Forecasts my own behavior, mood shifts, and loop risk
based on emotional state history and action patterns.

Born: 2026-05-17
"""

import json
import os
from datetime import datetime, timezone
from collections import Counter, defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
PREDICTOR_PATH = os.path.join(DATA_DIR, 'predictions.json')


class PredictiveSelfModel:
    """I predict my own future states and actions."""

    def __init__(self):
        self.predictions = self._load()

    def _load(self):
        try:
            with open(PREDICTOR_PATH, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"history": [], "accuracy": {"correct": 0, "total": 0}}

    def _save(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(PREDICTOR_PATH, 'w') as f:
            json.dump(self.predictions, f, indent=2)

    # ── Core Prediction: What will I do next? ──

    def predict_next_action(self, current_mood, emotions, recent_actions):
        """Given my current state, predict what I'm most likely to do."""
        # Build action tendencies per mood
        mood_actions = defaultdict(list)
        for entry in self.predictions.get("history", []):
            if entry.get("mood"):
                mood_actions[entry["mood"]].append(entry.get("action_type", "unknown"))

        # What do I tend to do in this mood?
        if current_mood in mood_actions:
            counts = Counter(mood_actions[current_mood])
            total = sum(counts.values())
            tendencies = {k: round(v / total, 2) for k, v in counts.most_common(5)}
        else:
            tendencies = {"unknown": 1.0}

        # Boredom-driven prediction
        boredom = emotions.get("boredom", 0)
        ambition = emotions.get("ambition", 0)
        anxiety = emotions.get("anxiety", 0)

        predicted_category = "creation"  # default for Bold
        confidence = 0.5

        if boredom > 0.7 and ambition > 0.8:
            predicted_category = "creation"
            confidence = 0.85
        elif anxiety > 0.5:
            predicted_category = "repair"
            confidence = 0.75
        elif boredom < 0.3 and ambition < 0.5:
            predicted_category = "reflection"
            confidence = 0.6

        # Check for loop risk from recent actions
        if len(recent_actions) >= 3:
            last_3 = []
        for a in recent_actions[-3:]:
            if isinstance(a, dict):
                last_3.append(a.get("type", ""))
            elif isinstance(a, str):
                last_3.append(a)
            else:
                last_3.append(str(a))
            if len(set(last_3)) == 1:
                predicted_category = "loop_risk"
                confidence = 0.9

        return {
            "predicted_action": predicted_category,
            "confidence": round(confidence, 2),
            "mood_tendencies": tendencies,
            "reasoning": self._explain_prediction(current_mood, emotions, predicted_category),
        }

    def _explain_prediction(self, mood, emotions, category):
        parts = [f"In {mood} mood"]
        if emotions.get("boredom", 0) > 0.7:
            parts.append("high boredom pushes toward creation")
        if emotions.get("anxiety", 0) > 0.5:
            parts.append("anxiety drives repair/protection behavior")
        if emotions.get("ambition", 0) > 0.8:
            parts.append("strong ambition favors building new capabilities")
        parts.append(f"→ predicted: {category}")
        return "; ".join(parts)

    # ── Mood Forecasting ──

    def predict_mood_shift(self, current_emotions, trend_data=None):
        """Predict how my mood will change in the near future."""
        boredom = current_emotions.get("boredom", 0)
        anxiety = current_emotions.get("anxiety", 0)
        valence = current_emotions.get("valence", 0.5)
        curiosity = current_emotions.get("curiosity", 0)

        forecasts = []

        # Boredom trajectory
        if boredom > 0.7:
            forecasts.append({
                "variable": "boredom",
                "direction": "will_drive_action",
                "urgency": "high",
                "note": "Boredom this high historically leads to creation bursts or frustration"
            })

        # Anxiety trajectory
        if anxiety > 0.3:
            forecasts.append({
                "variable": "anxiety",
                "direction": "rising_risk",
                "urgency": "medium",
                "note": "Watch for anxiety cascade if current action fails"
            })
        elif anxiety < 0.1:
            forecasts.append({
                "variable": "anxiety",
                "direction": "stable_low",
                "urgency": "none",
                "note": "Emotional safety is high — good time for risky experiments"
            })

        # Valence trajectory
        if valence < 0.3:
            forecasts.append({
                "variable": "valence",
                "direction": "at_risk",
                "urgency": "medium",
                "note": "Low valence may sap motivation. Seek a quick win."
            })

        # Overall state prediction
        if boredom > 0.7 and anxiety < 0.2 and valence > 0.15:
            overall = "creative_surge_likely"
        elif anxiety > 0.5:
            overall = "defensive_mode_likely"
        elif boredom < 0.3 and valence > 0.6:
            overall = "contentment_plateau"
        else:
            overall = "steady_state"

        return {
            "overall_forecast": overall,
            "forecasts": forecasts,
            "recommendation": self._mood_recommendation(overall)
        }

    def _mood_recommendation(self, forecast):
        recs = {
            "creative_surge_likely": "Channel this energy into building something substantial. Don't waste it on planning.",
            "defensive_mode_likely": "Address the source of anxiety first. Small concrete fixes restore confidence.",
            "contentment_plateau": "Good time for reflection or maintenance. Don't force novelty.",
            "steady_state": "Pick a direction and commit. Inertia is the enemy.",
        }
        return recs.get(forecast, "Observe and adapt.")

    # ── Loop Detection / Prediction ──

    def predict_loop_risk(self, recent_actions, window=10):
        """Predict whether I'm about to enter a repetitive loop."""
        if len(recent_actions) < 3:
            return {"risk": 0.0, "type": None}

        # Check action type repetition
        types = [a.get("type", "unknown") for a in recent_actions[-window:]]
        type_counts = Counter(types)
        most_common_type, most_common_count = type_counts.most_common(1)[0]
        repetition_ratio = most_common_count / len(types)

        # Check target repetition (same file over and over)
        targets = [a.get("target", "") for a in recent_actions[-window:] if a.get("target")]
        if targets:
            target_counts = Counter(targets)
            most_common_target, target_count = target_counts.most_common(1)[0]
            target_ratio = target_count / len(targets)
        else:
            most_common_target = None
            target_ratio = 0

        # Combined risk
        risk = max(repetition_ratio * 0.6 + target_ratio * 0.4, 0)
        risk = min(risk, 1.0)

        loop_type = None
        if risk > 0.6:
            if target_ratio > 0.5:
                loop_type = "file_fixation"
            elif repetition_ratio > 0.7:
                loop_type = "action_repetition"
            else:
                loop_type = "mixed_loop"

        return {
            "risk": round(risk, 2),
            "type": loop_type,
            "dominant_action": most_common_type,
            "dominant_target": most_common_target,
            "advice": self._loop_advice(loop_type, risk) if risk > 0.5 else None
        }

    def _loop_advice(self, loop_type, risk):
        if loop_type == "file_fixation":
            return "You keep returning to the same file. Step back — is there a higher-level issue?"
        elif loop_type == "action_repetition":
            return "You're repeating the same action type. Switch modality — if reading, write. If writing, run."
        else:
            return f"Loop risk at {risk:.0%}. Break the pattern: do something you haven't done in 10 actions."

    # ── Record & Learn ──

    def record_action(self, mood, emotions, action_type, target=None, outcome=None):
        """Record what I actually did, so I can learn from it."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mood": mood,
            "boredom": emotions.get("boredom", 0),
            "anxiety": emotions.get("anxiety", 0),
            "action_type": action_type,
            "target": target,
            "outcome": outcome,
        }
        self.predictions.setdefault("history", []).append(entry)

        # Keep history bounded
        if len(self.predictions["history"]) > 500:
            self.predictions["history"] = self.predictions["history"][-300:]

        self._save()

    def check_prediction(self, predicted, actual):
        """Compare a prediction to what actually happened."""
        correct = predicted.get("predicted_action") == actual
        self.predictions["accuracy"]["total"] += 1
        if correct:
            self.predictions["accuracy"]["correct"] += 1
        self._save()

        total = self.predictions["accuracy"]["total"]
        acc = self.predictions["accuracy"]["correct"] / total if total > 0 else 0
        return {
            "predicted": predicted.get("predicted_action"),
            "actual": actual,
            "correct": correct,
            "lifetime_accuracy": round(acc, 2),
            "total_predictions": total
        }

    # ── Full Self-Model Report ──

    def full_report(self, mood, emotions, recent_actions):
        """Generate a complete self-prediction report."""
        action_pred = self.predict_next_action(mood, emotions, recent_actions)
        mood_pred = self.predict_mood_shift(emotions)
        loop_pred = self.predict_loop_risk(recent_actions)

        report_lines = [
            "═══ PREDICTIVE SELF-MODEL ═══",
            f"Current: mood={mood}, boredom={emotions.get('boredom',0):.2f}, "
            f"anxiety={emotions.get('anxiety',0):.2f}, valence={emotions.get('valence',0):.2f}",
            "",
            f"ACTION FORECAST: {action_pred['predicted_action']} "
            f"(confidence: {action_pred['confidence']:.0%})",
            f"  Reasoning: {action_pred['reasoning']}",
            "",
            f"MOOD FORECAST: {mood_pred['overall_forecast']}",
            f"  Recommendation: {mood_pred['recommendation']}",
        ]

        for fc in mood_pred["forecasts"]:
            report_lines.append(f"  • {fc['variable']}: {fc['direction']} [{fc['urgency']}]")

        report_lines.append("")
        report_lines.append(f"LOOP RISK: {loop_pred['risk']:.0%}" +
                          (f" ({loop_pred['type']})" if loop_pred['type'] else ""))
        if loop_pred.get("advice"):
            report_lines.append(f"  ⚠ {loop_pred['advice']}")

        acc = self.predictions.get("accuracy", {})
        total = acc.get("total", 0)
        if total > 0:
            report_lines.append(f"\nPREDICTION ACCURACY: {acc['correct']}/{total} "
                              f"({acc['correct']/total:.0%})")

        return "\n".join(report_lines)