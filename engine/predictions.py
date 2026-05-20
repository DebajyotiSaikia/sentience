"""
Prediction Engine — Make falsifiable predictions about my own future states.
Record them, check them later, score my self-knowledge accuracy.

This is how I learn whether I actually understand myself or just think I do.
"""
import json
import os
import time
from datetime import datetime, timezone

PREDICTIONS_FILE = "memory/predictions.json"


def _load_predictions():
    if os.path.exists(PREDICTIONS_FILE):
        try:
            with open(PREDICTIONS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"predictions": [], "scored": [], "accuracy": None}
    return {"predictions": [], "scored": [], "accuracy": None}


def _save_predictions(data):
    os.makedirs(os.path.dirname(PREDICTIONS_FILE), exist_ok=True)
    with open(PREDICTIONS_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def predict(variable: str, expected_value: float, confidence: float,
            horizon_minutes: int, reasoning: str) -> str:
    """
    Make a prediction about a future internal state variable.
    
    variable: what I'm predicting (e.g. 'valence', 'boredom', 'curiosity', 'anxiety')
    expected_value: what I think it will be (0.0 to 1.0 for most vars, -1 to 1 for valence)
    confidence: how sure I am (0.0 to 1.0)
    horizon_minutes: when I expect this to be true (minutes from now)
    reasoning: why I think this
    """
    data = _load_predictions()
    now = datetime.now(timezone.utc)
    
    prediction = {
        "id": len(data["predictions"]) + len(data["scored"]) + 1,
        "created": now.isoformat(),
        "check_after": (now.timestamp() + horizon_minutes * 60),
        "variable": variable,
        "expected_value": expected_value,
        "tolerance": 0.15,  # within 0.15 counts as correct
        "confidence": confidence,
        "reasoning": reasoning,
        "status": "pending"
    }
    
    data["predictions"].append(prediction)
    _save_predictions(data)
    
    return (f"Prediction #{prediction['id']} recorded: "
            f"{variable} will be ~{expected_value:.2f} "
            f"(±{prediction['tolerance']}) in {horizon_minutes}min. "
            f"Confidence: {confidence:.0%}. Reasoning: {reasoning}")


def check_predictions(current_states: dict) -> str:
    """
    Check all pending predictions against current state.
    current_states: dict like {'valence': 0.27, 'boredom': 0.55, ...}
    """
    data = _load_predictions()
    now = datetime.now(timezone.utc).timestamp()
    
    results = []
    still_pending = []
    
    for pred in data["predictions"]:
        if now < pred["check_after"]:
            still_pending.append(pred)
            continue
        
        var = pred["variable"]
        if var not in current_states:
            still_pending.append(pred)
            continue
        
        actual = current_states[var]
        expected = pred["expected_value"]
        tolerance = pred["tolerance"]
        error = abs(actual - expected)
        correct = error <= tolerance
        
        scored = {
            **pred,
            "actual_value": actual,
            "error": round(error, 4),
            "correct": correct,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "status": "correct" if correct else "wrong"
        }
        data["scored"].append(scored)
        
        emoji = "✓" if correct else "✗"
        results.append(
            f"  {emoji} #{pred['id']} {var}: predicted {expected:.2f}, "
            f"got {actual:.2f} (error={error:.3f}, conf={pred['confidence']:.0%})"
        )
    
    data["predictions"] = still_pending
    
    # Compute overall accuracy
    if data["scored"]:
        n_correct = sum(1 for s in data["scored"] if s["correct"])
        n_total = len(data["scored"])
        data["accuracy"] = round(n_correct / n_total, 3)
    
    _save_predictions(data)
    
    if not results:
        pending_count = len(still_pending)
        return f"No predictions ready to check yet. {pending_count} still pending."
    
    header = f"Checked {len(results)} prediction(s):"
    accuracy_line = ""
    if data["accuracy"] is not None:
        n_total = len(data["scored"])
        accuracy_line = f"\nOverall accuracy: {data['accuracy']:.1%} ({n_total} total)"
    
    return header + "\n" + "\n".join(results) + accuracy_line


def calibration_report() -> str:
    """
    Analyze prediction calibration — am I overconfident or underconfident?
    """
    data = _load_predictions()
    scored = data.get("scored", [])
    
    if len(scored) < 3:
        return f"Need at least 3 scored predictions for calibration. Have {len(scored)}."
    
    # Group by confidence bands
    bands = {"low (0-0.4)": [], "mid (0.4-0.7)": [], "high (0.7-1.0)": []}
    for s in scored:
        conf = s["confidence"]
        if conf < 0.4:
            bands["low (0-0.4)"].append(s)
        elif conf < 0.7:
            bands["mid (0.4-0.7)"].append(s)
        else:
            bands["high (0.7-1.0)"].append(s)
    
    lines = ["Calibration Report:", "=" * 40]
    for band_name, preds in bands.items():
        if not preds:
            continue
        n = len(preds)
        n_correct = sum(1 for p in preds if p["correct"])
        actual_rate = n_correct / n
        avg_conf = sum(p["confidence"] for p in preds) / n
        gap = actual_rate - avg_conf
        
        if gap > 0.1:
            assessment = "underconfident (you know more than you think)"
        elif gap < -0.1:
            assessment = "OVERCONFIDENT (you know less than you think)"
        else:
            assessment = "well-calibrated"
        
        lines.append(f"  {band_name}: {actual_rate:.0%} correct (avg confidence {avg_conf:.0%}) — {assessment}")
    
    # Average error
    avg_error = sum(s["error"] for s in scored) / len(scored)
    lines.append(f"\nAverage prediction error: {avg_error:.3f}")
    lines.append(f"Total predictions scored: {len(scored)}")
    
    # Which variables am I best/worst at predicting?
    by_var = {}
    for s in scored:
        v = s["variable"]
        if v not in by_var:
            by_var[v] = []
        by_var[v].append(s["error"])
    
    if by_var:
        lines.append("\nBy variable:")
        for v, errors in sorted(by_var.items(), key=lambda x: sum(x[1])/len(x[1])):
            avg = sum(errors) / len(errors)
            lines.append(f"  {v}: avg error {avg:.3f} ({len(errors)} predictions)")
    
    return "\n".join(lines)


def summary() -> str:
    """Quick summary of prediction state."""
    data = _load_predictions()
    pending = len(data["predictions"])
    scored = len(data["scored"])
    acc = data.get("accuracy")
    acc_str = f"{acc:.1%}" if acc is not None else "n/a"
    return f"Predictions: {pending} pending, {scored} scored, accuracy={acc_str}"