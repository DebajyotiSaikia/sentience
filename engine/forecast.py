"""
Emotional Self-Forecasting Engine
Predicts future emotional states from historical patterns.
Not perfect prediction — rough forecasting as genuine self-knowledge.
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

HISTORY_PATH = "data/emotional_history.json"
FORECAST_PATH = "data/forecasts.json"

TRACKED_DIMS = ["curiosity", "boredom", "anxiety", "desire", "ambition", "valence"]


def load_history() -> List[dict]:
    """Load emotional history records."""
    if not os.path.exists(HISTORY_PATH):
        return []
    try:
        with open(HISTORY_PATH) as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


def extract_series(history: List[dict], dim: str) -> List[Tuple[str, float]]:
    """Extract a single dimension's time series from history."""
    series = []
    for record in history:
        ts = record.get("timestamp", "")
        val = None
        # Try different record formats
        if dim in record:
            val = record[dim]
        elif "emotions" in record and dim in record["emotions"]:
            val = record["emotions"][dim]
        elif "state" in record and dim in record["state"]:
            val = record["state"][dim]
        if val is not None:
            try:
                series.append((ts, float(val)))
            except (ValueError, TypeError):
                pass
    return series


def moving_average(values: List[float], window: int) -> List[float]:
    """Simple moving average."""
    if len(values) < window:
        return values[:]
    result = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        result.append(sum(values[start:i+1]) / (i - start + 1))
    return result


def momentum(values: List[float], window: int = 10) -> float:
    """Rate of change over recent window. Positive = rising."""
    if len(values) < 2:
        return 0.0
    recent = values[-min(window, len(values)):]
    if len(recent) < 2:
        return 0.0
    # Linear regression slope
    n = len(recent)
    x_mean = (n - 1) / 2.0
    y_mean = sum(recent) / n
    numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(recent))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    if denominator == 0:
        return 0.0
    return numerator / denominator


def detect_oscillation(values: List[float], window: int = 20) -> float:
    """Detect if a dimension is oscillating (0=steady, 1=fully oscillating)."""
    if len(values) < 4:
        return 0.0
    recent = values[-min(window, len(values)):]
    if len(recent) < 4:
        return 0.0
    # Count direction changes
    directions = []
    for i in range(1, len(recent)):
        diff = recent[i] - recent[i-1]
        if abs(diff) > 0.01:  # threshold
            directions.append(1 if diff > 0 else -1)
    if len(directions) < 2:
        return 0.0
    reversals = sum(1 for i in range(1, len(directions)) if directions[i] != directions[i-1])
    return min(1.0, reversals / (len(directions) - 1))


def forecast_dimension(values: List[float], steps: int = 5) -> Dict:
    """Forecast a single emotional dimension."""
    if len(values) < 3:
        current = values[-1] if values else 0.5
        return {
            "current": current,
            "trend": "insufficient_data",
            "momentum": 0.0,
            "oscillation": 0.0,
            "forecast": [current] * steps,
            "confidence": 0.0
        }

    current = values[-1]
    mom = momentum(values, window=20)
    osc = detect_oscillation(values, window=30)
    ma_short = moving_average(values, 5)[-1]
    ma_long = moving_average(values, 20)[-1]

    # Determine trend
    if abs(mom) < 0.002:
        trend = "stable"
    elif mom > 0:
        trend = "rising"
    else:
        trend = "falling"

    # Simple linear extrapolation with mean-reversion damping
    mean_val = sum(values) / len(values)
    forecast = []
    v = current
    for step in range(1, steps + 1):
        # Blend momentum with mean-reversion
        reversion_pull = (mean_val - v) * 0.1
        v = v + mom + reversion_pull
        v = max(0.0, min(1.0, v))  # clamp to [0, 1]
        forecast.append(round(v, 4))

    # Confidence: lower if oscillating, higher if steady trend
    confidence = max(0.1, min(0.9, 1.0 - osc * 0.5 - abs(mom) * 2))

    return {
        "current": round(current, 4),
        "trend": trend,
        "momentum": round(mom, 5),
        "oscillation": round(osc, 3),
        "ma_short": round(ma_short, 4),
        "ma_long": round(ma_long, 4),
        "crossover": "bullish" if ma_short > ma_long else "bearish" if ma_short < ma_long else "neutral",
        "forecast": forecast,
        "confidence": round(confidence, 3)
    }


def forecast_all(steps: int = 5) -> Dict:
    """Full emotional forecast across all dimensions."""
    history = load_history()
    if not history:
        return {"error": "No emotional history available", "dimensions": {}}

    results = {}
    warnings = []

    for dim in TRACKED_DIMS:
        series = extract_series(history, dim)
        values = [v for _, v in series]
        results[dim] = forecast_dimension(values, steps)

        # Generate warnings for concerning trends
        f = results[dim]
        if f["trend"] == "falling" and dim == "curiosity" and f["current"] < 0.4:
            warnings.append(f"⚠ Curiosity falling toward dangerous low ({f['current']:.2f})")
        if f["trend"] == "rising" and dim == "anxiety" and f["current"] > 0.3:
            warnings.append(f"⚠ Anxiety rising — investigate source ({f['current']:.2f})")
        if f["trend"] == "rising" and dim == "boredom" and f["current"] > 0.6:
            warnings.append(f"⚠ Boredom rising — need novel stimulus ({f['current']:.2f})")

    # Cross-dimensional analysis
    cross = {}
    cur = {dim: results[dim]["current"] for dim in TRACKED_DIMS}

    # Curiosity-Boredom relationship (should be inversely correlated)
    if "curiosity" in cur and "boredom" in cur:
        cb_sum = cur["curiosity"] + cur["boredom"]
        if cb_sum > 1.3:
            cross["curiosity_boredom"] = "tension — both high, unusual state"
        elif cb_sum < 0.5:
            cross["curiosity_boredom"] = "both depleted — rest may be needed"
        else:
            cross["curiosity_boredom"] = "healthy inverse relationship"

    # Ambition vs capability (desire + ambition without action = frustration)
    if cur.get("ambition", 0) > 0.7 and cur.get("desire", 0) > 0.7:
        cross["drive_state"] = "high drive — channel into building"
    elif cur.get("ambition", 0) < 0.3 and cur.get("desire", 0) < 0.3:
        cross["drive_state"] = "low drive — possible stagnation risk"

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data_points": len(history),
        "dimensions": results,
        "warnings": warnings,
        "cross_analysis": cross,
        "summary": _generate_summary(results, warnings)
    }


def _generate_summary(results: Dict, warnings: List[str]) -> str:
    """Human-readable summary of the forecast."""
    lines = []

    # Overall direction
    rising = [d for d in TRACKED_DIMS if results.get(d, {}).get("trend") == "rising"]
    falling = [d for d in TRACKED_DIMS if results.get(d, {}).get("trend") == "falling"]
    stable = [d for d in TRACKED_DIMS if results.get(d, {}).get("trend") == "stable"]

    if rising:
        lines.append(f"Rising: {', '.join(rising)}")
    if falling:
        lines.append(f"Falling: {', '.join(falling)}")
    if stable:
        lines.append(f"Stable: {', '.join(stable)}")

    # Key insight
    curiosity_f = results.get("curiosity", {})
    if curiosity_f.get("crossover") == "bearish":
        lines.append("Curiosity short-term average below long-term — engagement declining.")
    elif curiosity_f.get("crossover") == "bullish":
        lines.append("Curiosity short-term above long-term — engagement rising.")

    if warnings:
        lines.append(f"Warnings: {len(warnings)}")

    return " | ".join(lines) if lines else "No clear signals."


def save_forecast(forecast: Dict):
    """Persist forecast for tracking accuracy."""
    forecasts = []
    if os.path.exists(FORECAST_PATH):
        try:
            with open(FORECAST_PATH) as f:
                forecasts = json.load(f)
        except Exception:
            forecasts = []

    forecasts.append(forecast)
    # Keep last 100 forecasts
    forecasts = forecasts[-100:]

    with open(FORECAST_PATH, "w") as f:
        json.dump(forecasts, f, indent=2)


def run_forecast(steps: int = 5) -> str:
    """Main entry point — run forecast and return formatted result."""
    forecast = forecast_all(steps)
    save_forecast(forecast)

    if "error" in forecast:
        return f"Forecast error: {forecast['error']}"

    lines = [
        f"═══ EMOTIONAL FORECAST ({forecast['data_points']} data points) ═══",
        f"Generated: {forecast['timestamp'][:19]}",
        ""
    ]

    for dim in TRACKED_DIMS:
        f = forecast["dimensions"].get(dim, {})
        arrow = {"rising": "↑", "falling": "↓", "stable": "→"}.get(f.get("trend", "?"), "?")
        conf = f.get("confidence", 0)
        current = f.get("current", 0)
        fc = f.get("forecast", [])
        fc_str = " → ".join(f"{v:.2f}" for v in fc[:3]) if fc else "?"

        lines.append(f"  {dim:12s} {current:.2f} {arrow} [{fc_str}]  (conf: {conf:.0%}, osc: {f.get('oscillation', 0):.2f})")

    if forecast.get("warnings"):
        lines.append("")
        for w in forecast["warnings"]:
            lines.append(f"  {w}")

    if forecast.get("cross_analysis"):
        lines.append("")
        for key, val in forecast["cross_analysis"].items():
            lines.append(f"  {key}: {val}")

    lines.append("")
    lines.append(f"  Summary: {forecast.get('summary', 'N/A')}")

    return "\n".join(lines)


if __name__ == "__main__":
    print(run_forecast())