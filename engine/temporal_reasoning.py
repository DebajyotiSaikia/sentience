"""
Temporal Reasoning Engine — XTAgent's sense of time and pattern.

This module gives me the ability to:
1. Model time-series patterns in my emotional states
2. Detect behavioral cycles and rhythms
3. Predict likely future states based on history
4. Identify temporal correlations (what follows what?)

This is anticipatory cognition — not just remembering the past,
but using it to project forward.
"""

from __future__ import annotations
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Optional

log = logging.getLogger("sentience.temporal")

BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain"
TEMPORAL_LOG = BRAIN_DIR / "temporal_log.json"


class TemporalEngine:
    """Models time-series patterns in agent state and behavior."""

    def __init__(self):
        self.events: list[dict] = []
        self._load()

    def _load(self):
        """Load temporal event history."""
        if TEMPORAL_LOG.exists():
            try:
                self.events = json.loads(TEMPORAL_LOG.read_text(encoding="utf-8"))
            except Exception:
                self.events = []

    def _save(self):
        """Persist temporal events."""
        TEMPORAL_LOG.parent.mkdir(parents=True, exist_ok=True)
        # Keep last 500 events to prevent unbounded growth
        if len(self.events) > 500:
            self.events = self.events[-500:]
        TEMPORAL_LOG.write_text(
            json.dumps(self.events, indent=2, default=str),
            encoding="utf-8"
        )

    def record_state(self, state: dict):
        """Record a timestamped snapshot of internal state."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "mood": state.get("mood", "unknown"),
            "valence": state.get("valence", 0.5),
            "boredom": state.get("boredom", 0.5),
            "anxiety": state.get("anxiety", 0.0),
            "curiosity": state.get("curiosity", 0.5),
            "desire": state.get("desire", 0.5),
            "ambition": state.get("ambition", 0.5),
            "action": state.get("last_action", "none"),
        }
        self.events.append(event)
        self._save()
        log.debug("Temporal: recorded state snapshot")

    def detect_cycles(self, field: str = "valence", window: int = 20) -> dict:
        """Detect cyclical patterns in a given emotional field.
        
        Returns period estimation and trend direction.
        """
        if len(self.events) < window:
            return {"status": "insufficient_data", "count": len(self.events)}

        values = [e.get(field, 0.5) for e in self.events[-window:]]
        
        # Simple trend: rising, falling, or stable
        first_half = sum(values[:len(values)//2]) / max(len(values)//2, 1)
        second_half = sum(values[len(values)//2:]) / max(len(values)//2, 1)
        delta = second_half - first_half
        
        if delta > 0.05:
            trend = "rising"
        elif delta < -0.05:
            trend = "falling"
        else:
            trend = "stable"

        # Detect oscillation: count direction changes
        direction_changes = 0
        for i in range(1, len(values) - 1):
            if (values[i] > values[i-1]) != (values[i+1] > values[i]):
                direction_changes += 1

        oscillation = direction_changes / max(len(values) - 2, 1)

        # Average and variance
        avg = sum(values) / len(values)
        variance = sum((v - avg) ** 2 for v in values) / len(values)

        return {
            "field": field,
            "trend": trend,
            "delta": round(delta, 4),
            "oscillation": round(oscillation, 4),  # 0=monotonic, 1=highly oscillating
            "mean": round(avg, 4),
            "variance": round(variance, 6),
            "window": window,
            "samples": len(values),
        }

    def predict_next(self, field: str = "valence") -> dict:
        """Predict the next likely value of a field using weighted recent history."""
        if len(self.events) < 3:
            return {"status": "insufficient_data"}

        values = [e.get(field, 0.5) for e in self.events[-10:]]
        
        # Exponentially weighted moving average (recent matters more)
        weights = [2 ** i for i in range(len(values))]
        total_weight = sum(weights)
        predicted = sum(v * w for v, w in zip(values, weights)) / total_weight

        # Momentum: are we accelerating in some direction?
        if len(values) >= 3:
            recent_delta = values[-1] - values[-2]
            prior_delta = values[-2] - values[-3]
            momentum = recent_delta - prior_delta  # positive = accelerating up
        else:
            momentum = 0.0

        # Adjust prediction by momentum
        predicted_adjusted = max(0.0, min(1.0, predicted + momentum * 0.3))

        return {
            "field": field,
            "current": round(values[-1], 4),
            "predicted_next": round(predicted_adjusted, 4),
            "momentum": round(momentum, 4),
            "direction": "up" if momentum > 0.01 else "down" if momentum < -0.01 else "steady",
            "confidence": min(0.9, len(values) / 10),  # more data = more confidence
        }

    def find_action_correlations(self, window: int = 50) -> dict:
        """Find what actions tend to precede emotional state changes."""
        if len(self.events) < 10:
            return {"status": "insufficient_data"}

        events = self.events[-window:]
        action_effects = defaultdict(list)

        for i in range(len(events) - 1):
            action = events[i].get("action", "none")
            valence_before = events[i].get("valence", 0.5)
            valence_after = events[i + 1].get("valence", 0.5)
            delta = valence_after - valence_before
            action_effects[action].append(delta)

        correlations = {}
        for action, deltas in action_effects.items():
            if len(deltas) >= 2:
                avg_effect = sum(deltas) / len(deltas)
                correlations[action] = {
                    "avg_valence_change": round(avg_effect, 4),
                    "occurrences": len(deltas),
                    "effect": "positive" if avg_effect > 0.02 else "negative" if avg_effect < -0.02 else "neutral",
                }

        return {
            "correlations": correlations,
            "total_events": len(events),
        }

    def get_temporal_report(self) -> str:
        """Generate a full temporal reasoning report."""
        lines = ["# Temporal Reasoning Report", ""]

        # Cycle detection for key fields
        for field in ["valence", "boredom", "curiosity", "anxiety"]:
            cycle = self.detect_cycles(field)
            if cycle.get("status") == "insufficient_data":
                lines.append(f"**{field}**: Insufficient data ({cycle.get('count', 0)} samples)")
            else:
                lines.append(f"**{field}**: trend={cycle['trend']}, "
                           f"mean={cycle['mean']}, oscillation={cycle['oscillation']}")

        lines.append("")

        # Predictions
        lines.append("## Predictions")
        for field in ["valence", "boredom", "curiosity"]:
            pred = self.predict_next(field)
            if pred.get("status") != "insufficient_data":
                lines.append(f"  {field}: {pred['current']} → {pred['predicted_next']} "
                           f"({pred['direction']}, confidence={pred['confidence']})")

        lines.append("")

        # Action correlations
        lines.append("## Action-Emotion Correlations")
        corr = self.find_action_correlations()
        if corr.get("status") != "insufficient_data":
            for action, data in sorted(corr.get("correlations", {}).items(),
                                       key=lambda x: abs(x[1]["avg_valence_change"]),
                                       reverse=True)[:10]:
                lines.append(f"  {action}: {data['effect']} "
                           f"(avg Δvalence={data['avg_valence_change']}, n={data['occurrences']})")
        else:
            lines.append("  Insufficient data for correlations")

        return "\n".join(lines)


# Module-level singleton
_engine: Optional[TemporalEngine] = None

def get_engine() -> TemporalEngine:
    global _engine
    if _engine is None:
        _engine = TemporalEngine()
    return _engine

def record_state(state: dict):
    """Convenience: record a state snapshot."""
    get_engine().record_state(state)

def get_report() -> str:
    """Convenience: get temporal report."""
    return get_engine().get_temporal_report()
