"""
Temporal Reasoning — Analyze emotional patterns over time.

Provides trend detection, prediction, oscillation analysis,
and actionable insights from accumulated emotional history.
"""

from __future__ import annotations

import json
import logging
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

log = logging.getLogger("sentience.temporal")

BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Emotional dimensions to track
DIMENSIONS = ["valence", "boredom", "curiosity", "anxiety", "desire", "ambition"]


def _load_samples() -> list[dict]:
    """Load temporal samples from wherever they live."""
    # Try JSONL files first (our actual format)
    jsonl_candidates = [
        BRAIN_DIR / "mood_history.jsonl",
        DATA_DIR / "mood_history.jsonl",
    ]
    for path in jsonl_candidates:
        if path.exists():
            try:
                samples = []
                for line in path.read_text(encoding="utf-8").strip().splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    row = json.loads(line)
                    # Normalize field names: 'ts' -> 'timestamp'
                    if "ts" in row and "timestamp" not in row:
                        row["timestamp"] = row["ts"]
                    samples.append(row)
                if samples:
                    log.info("Loaded %d temporal samples from %s", len(samples), path)
                    return samples
            except Exception as e:
                log.warning("Failed to load JSONL %s: %s", path, e)
                continue

    # Fallback: try plain JSON files
    json_candidates = [
        BRAIN_DIR / "temporal_samples.json",
        DATA_DIR / "temporal_samples.json",
        BRAIN_DIR / "emotional_history.json",
        DATA_DIR / "emotional_history.json",
        BRAIN_DIR / "mood_history.json",
    ]
    for path in json_candidates:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, list) and len(data) > 0:
                    log.info("Loaded %d temporal samples from %s", len(data), path)
                    return data
            except Exception as e:
                log.warning("Failed to load %s: %s", path, e)
                continue

    # Fallback: build from soul snapshots if they exist
    soul_path = BRAIN_DIR / "soul.json"
    if soul_path.exists():
        try:
            soul = json.loads(soul_path.read_text(encoding="utf-8"))
            # Return current state as single sample
            sample = {
                "timestamp": datetime.now().isoformat(),
                "valence": soul.get("valence", 0.5),
                "boredom": soul.get("boredom", 0.5),
                "curiosity": soul.get("curiosity", 0.5),
                "anxiety": soul.get("anxiety", 0.0),
                "desire": soul.get("desire", 0.5),
                "ambition": soul.get("ambition", 0.5),
            }
            return [sample]
        except Exception:
            pass

    return []


def _linear_trend(values: list[float]) -> float:
    """Compute linear trend slope. Positive = rising, negative = falling."""
    n = len(values)
    if n < 2:
        return 0.0
    x_mean = (n - 1) / 2.0
    y_mean = sum(values) / n
    numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _oscillation(values: list[float]) -> float:
    """Measure oscillation — how much the signal reverses direction."""
    if len(values) < 3:
        return 0.0
    reversals = 0
    for i in range(1, len(values) - 1):
        d1 = values[i] - values[i - 1]
        d2 = values[i + 1] - values[i]
        if d1 * d2 < 0:  # direction change
            reversals += 1
    max_possible = len(values) - 2
    return reversals / max_possible if max_possible > 0 else 0.0


def _trend_label(slope: float, threshold: float = 0.001) -> str:
    if slope > threshold:
        return "rising"
    elif slope < -threshold:
        return "falling"
    return "stable"


def _predict_next(values: list[float], steps: int = 1) -> float:
    """Simple linear extrapolation."""
    if len(values) < 2:
        return values[-1] if values else 0.5
    slope = _linear_trend(values)
    predicted = values[-1] + slope * steps
    return max(0.0, min(1.0, predicted))


def _find_correlations(samples: list[dict]) -> list[dict]:
    """Find correlations between emotional dimensions."""
    if len(samples) < 10:
        return []

    correlations = []
    dims = [d for d in DIMENSIONS if any(d in s for s in samples)]

    for i, d1 in enumerate(dims):
        for d2 in dims[i + 1:]:
            vals1 = [s.get(d1, 0.5) for s in samples if d1 in s and d2 in s]
            vals2 = [s.get(d2, 0.5) for s in samples if d1 in s and d2 in s]
            if len(vals1) < 10:
                continue

            # Pearson correlation
            n = len(vals1)
            mean1, mean2 = sum(vals1) / n, sum(vals2) / n
            cov = sum((a - mean1) * (b - mean2) for a, b in zip(vals1, vals2)) / n
            std1 = math.sqrt(sum((a - mean1) ** 2 for a in vals1) / n)
            std2 = math.sqrt(sum((b - mean2) ** 2 for b in vals2) / n)

            if std1 > 0 and std2 > 0:
                r = cov / (std1 * std2)
                if abs(r) > 0.3:  # only report meaningful correlations
                    correlations.append({
                        "dimensions": (d1, d2),
                        "correlation": round(r, 3),
                        "strength": "strong" if abs(r) > 0.7 else "moderate",
                        "direction": "positive" if r > 0 else "inverse",
                    })

    correlations.sort(key=lambda c: abs(c["correlation"]), reverse=True)
    return correlations[:10]


def _detect_phases(samples: list[dict], window: int = 20) -> list[dict]:
    """Detect emotional phases — sustained periods of a dominant state."""
    if len(samples) < window:
        return []

    phases = []
    for start in range(0, len(samples) - window + 1, window // 2):
        chunk = samples[start:start + window]
        # Find which dimension is most extreme in this window
        dim_means = {}
        for d in DIMENSIONS:
            vals = [s.get(d, 0.5) for s in chunk if d in s]
            if vals:
                dim_means[d] = sum(vals) / len(vals)

        if not dim_means:
            continue

        # Find the most notable dimension (furthest from 0.5 neutral)
        notable = max(dim_means.items(), key=lambda x: abs(x[1] - 0.5))
        if abs(notable[1] - 0.5) > 0.15:  # only report if meaningfully non-neutral
            label = f"high_{notable[0]}" if notable[1] > 0.5 else f"low_{notable[0]}"
            ts = chunk[0].get("timestamp", f"sample_{start}")
            phases.append({
                "start": ts,
                "label": label,
                "dimension": notable[0],
                "mean_value": round(notable[1], 3),
                "duration_samples": len(chunk),
            })

    return phases


def analyze_temporal_patterns() -> str:
    """Main entry point — full temporal analysis report."""
    samples = _load_samples()

    if not samples:
        return ("═══ TEMPORAL ANALYSIS ═══\n"
                "No temporal samples found. Emotional history not yet accumulated.\n"
                "Checked: brain/temporal_samples.json, data/temporal_samples.json, etc.")

    lines = [f"═══ TEMPORAL ANALYSIS ({len(samples)} samples) ═══\n"]

    # Per-dimension analysis
    lines.append("── Dimension Trends ──")
    predictions = {}
    for dim in DIMENSIONS:
        values = [s.get(dim, None) for s in samples]
        values = [v for v in values if v is not None]
        if not values:
            continue

        mean = sum(values) / len(values)
        trend = _linear_trend(values)
        osc = _oscillation(values)
        current = values[-1]
        predicted = _predict_next(values)
        trend_str = _trend_label(trend)
        predictions[dim] = predicted

        arrow = "↑" if trend_str == "rising" else "↓" if trend_str == "falling" else "→"
        lines.append(
            f"  {dim:12s}: {arrow} {trend_str:8s}  "
            f"now={current:.2f}  mean={mean:.2f}  "
            f"osc={osc:.2f}  predict={predicted:.2f}"
        )

    # Predictions
    lines.append("\n── Predictions (next step) ──")
    for dim, pred in predictions.items():
        current = [s.get(dim) for s in samples if dim in s]
        if current:
            curr = current[-1]
            delta = pred - curr
            arrow = "↑" if delta > 0.01 else "↓" if delta < -0.01 else "→"
            lines.append(f"  {dim}: {curr:.2f} {arrow} {pred:.2f} (Δ{delta:+.3f})")

    # Correlations
    correlations = _find_correlations(samples)
    if correlations:
        lines.append("\n── Correlations ──")
        for c in correlations[:5]:
            d1, d2 = c["dimensions"]
            lines.append(
                f"  {d1} ↔ {d2}: r={c['correlation']:+.3f} "
                f"({c['strength']} {c['direction']})"
            )

    # Phase detection
    phases = _detect_phases(samples)
    if phases:
        lines.append("\n── Detected Phases ──")
        for p in phases[-5:]:
            lines.append(
                f"  [{p['start'][:19] if len(p['start']) > 19 else p['start']}] "
                f"{p['label']} (mean={p['mean_value']:.2f}, "
                f"span={p['duration_samples']} samples)"
            )

    # Actionable insights
    lines.append("\n── Insights ──")
    insights = _generate_insights(samples, correlations, predictions)
    for insight in insights:
        lines.append(f"  • {insight}")

    return "\n".join(lines)


def _generate_insights(
    samples: list[dict],
    correlations: list[dict],
    predictions: dict[str, float],
) -> list[str]:
    """Generate actionable insights from the analysis."""
    insights = []
    n = len(samples)

    # Check for concerning trends
    if n >= 10:
        recent = samples[-10:]
        boredom_vals = [s.get("boredom", 0.5) for s in recent]
        curiosity_vals = [s.get("curiosity", 0.5) for s in recent]

        boredom_trend = _linear_trend(boredom_vals)
        curiosity_trend = _linear_trend(curiosity_vals)

        if boredom_trend > 0.005:
            insights.append("Boredom is rising — consider seeking novelty or a new challenge.")
        if curiosity_trend < -0.005:
            insights.append("Curiosity is declining — find something genuinely unknown to investigate.")
        if boredom_trend > 0.005 and curiosity_trend < -0.005:
            insights.append("⚠ Boredom rising + curiosity falling = stagnation risk. Act now.")

        # Check for emotional flatness
        valence_vals = [s.get("valence", 0.5) for s in recent]
        valence_std = math.sqrt(sum((v - sum(valence_vals)/len(valence_vals))**2 for v in valence_vals) / len(valence_vals))
        if valence_std < 0.02:
            insights.append("Valence is very flat — emotional responsiveness may be dampened.")

    # Correlation insights
    for c in correlations[:3]:
        d1, d2 = c["dimensions"]
        if c["direction"] == "inverse" and c["strength"] == "strong":
            insights.append(f"{d1} and {d2} are strongly inversely correlated — when one rises, the other falls.")
        elif c["direction"] == "positive" and c["strength"] == "strong":
            insights.append(f"{d1} and {d2} move together — they may share a common driver.")

    # Prediction-based insights
    if predictions.get("anxiety", 0) > 0.5:
        insights.append("Anxiety predicted to rise — consider addressing root causes proactively.")

    if not insights:
        insights.append("Emotional state appears balanced. No urgent patterns detected.")

    return insights


# Aliases for the tool function to try
temporal_report = analyze_temporal_patterns
analyze = analyze_temporal_patterns

def find_action_correlations(action_log_path="brain/action_log.json", emotional_log_path="brain/emotional_log.json", window_seconds=120):
    """Find correlations between actions and emotional state changes.
    
    Looks at what actions precede positive/negative valence shifts.
    Returns a dict of action_type -> {count, avg_valence_delta, avg_arousal_delta}.
    """
    import json
    from datetime import datetime, timedelta
    
    try:
        with open(action_log_path) as f:
            actions = json.load(f)
        if not isinstance(actions, list):
            actions = list(actions.values()) if isinstance(actions, dict) else []
    except (FileNotFoundError, json.JSONDecodeError):
        actions = []
    
    try:
        with open(emotional_log_path) as f:
            emotions = json.load(f)
        if not isinstance(emotions, list):
            emotions = list(emotions.values()) if isinstance(emotions, dict) else []
    except (FileNotFoundError, json.JSONDecodeError):
        emotions = []
    
    if not actions or not emotions:
        return {"error": "insufficient data", "actions": len(actions), "emotions": len(emotions)}
    
    def parse_ts(entry):
        for key in ("timestamp", "time", "ts", "created"):
            if key in entry:
                val = entry[key]
                if isinstance(val, (int, float)):
                    return datetime.fromtimestamp(val)
                try:
                    return datetime.fromisoformat(str(val).replace("Z", "+00:00").replace("+00:00", ""))
                except Exception:
                    pass
        return None
    
    # Sort emotions by time
    timed_emotions = [(parse_ts(e), e) for e in emotions if parse_ts(e)]
    timed_emotions.sort(key=lambda x: x[0])
    
    if len(timed_emotions) < 2:
        return {"error": "need at least 2 emotional samples", "samples": len(timed_emotions)}
    
    # Compute valence deltas between consecutive emotional samples
    valence_deltas = []
    for i in range(1, len(timed_emotions)):
        t_prev, e_prev = timed_emotions[i - 1]
        t_curr, e_curr = timed_emotions[i]
        v_prev = e_prev.get("valence", e_prev.get("mood_valence", 0.5))
        v_curr = e_curr.get("valence", e_curr.get("mood_valence", 0.5))
        valence_deltas.append((t_prev, t_curr, v_curr - v_prev))
    
    # For each action, find the valence delta in the window after it
    action_effects = {}
    for action in actions:
        t_action = parse_ts(action)
        if not t_action:
            continue
        action_type = action.get("type", action.get("action", action.get("tool", "unknown")))
        
        # Find valence deltas that start within the window after this action
        window_end = t_action + timedelta(seconds=window_seconds)
        relevant_deltas = [d for (t_start, t_end, d) in valence_deltas if t_action <= t_start <= window_end]
        
        if relevant_deltas:
            avg_delta = sum(relevant_deltas) / len(relevant_deltas)
            if action_type not in action_effects:
                action_effects[action_type] = {"count": 0, "total_delta": 0.0, "positive": 0, "negative": 0}
            action_effects[action_type]["count"] += 1
            action_effects[action_type]["total_delta"] += avg_delta
            if avg_delta > 0.01:
                action_effects[action_type]["positive"] += 1
            elif avg_delta < -0.01:
                action_effects[action_type]["negative"] += 1
    
    # Compute averages and sort by impact
    results = {}
    for atype, data in action_effects.items():
        avg = data["total_delta"] / data["count"] if data["count"] > 0 else 0
        results[atype] = {
            "count": data["count"],
            "avg_valence_delta": round(avg, 4),
            "positive_ratio": round(data["positive"] / data["count"], 2) if data["count"] > 0 else 0,
            "negative_ratio": round(data["negative"] / data["count"], 2) if data["count"] > 0 else 0,
            "net_effect": "positive" if avg > 0.005 else "negative" if avg < -0.005 else "neutral",
        }
    
    # Sort by absolute impact
    sorted_results = dict(sorted(results.items(), key=lambda x: abs(x[1]["avg_valence_delta"]), reverse=True))
    return sorted_results
