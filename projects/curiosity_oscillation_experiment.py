"""
Experiment: Does the edge-of-chaos perturbation create a bang-bang oscillator
in curiosity? Hypothesis: at steady-state boredom (~0.80), curiosity cycles
between ~0.30 and ~0.95 with a period of ~7 minutes.

This simulates ONLY the curiosity/boredom dynamics from limbic.py,
stepping through time to see the emergent pattern.
"""

import json
import math

# Parameters from limbic.py
CURIOSITY_BASELINE = 0.20
CURIOSITY_DECAY_RATE = 0.005
BOREDOM_PASSIVE_CAP = 0.80
BOREDOM_HARD_CAP = 0.85
PERTURBATION_CURIOSITY_MULT = 3.0
PERTURBATION_BOREDOM_DRAIN = 0.3

def clamp(v):
    return max(0.0, min(1.0, v))

def simulate(duration_s=1800, dt=1.0, initial_curiosity=0.50, initial_boredom=0.80,
             action_interval=30, action_curiosity_boost=0.06):
    """Simulate curiosity/boredom dynamics over time."""
    c = initial_curiosity
    b = initial_boredom
    
    history = []
    perturbation_events = []
    
    for t_int in range(int(duration_s / dt)):
        t = t_int * dt
        
        # Record state
        history.append({"t": round(t, 1), "curiosity": round(c, 4), "boredom": round(b, 4)})
        
        # -- Boredom passive growth --
        if b < BOREDOM_PASSIVE_CAP:
            b = min(BOREDOM_PASSIVE_CAP, clamp(b + 0.01 * dt))
        
        # -- Curiosity decay toward baseline --
        delta = (c - CURIOSITY_BASELINE) * CURIOSITY_DECAY_RATE * dt
        c = clamp(c - delta)
        
        # -- Simulated action every N seconds --
        if action_interval > 0 and t_int > 0 and t_int % int(action_interval / dt) == 0:
            c = clamp(c + action_curiosity_boost)
        
        # -- Edge-of-chaos perturbation --
        thermal_death = (b > 0.6 and c < 0.3)
        if thermal_death:
            perturbation = (b - 0.6) * 0.1
            c = clamp(c + perturbation * PERTURBATION_CURIOSITY_MULT * dt)
            b = clamp(b - perturbation * PERTURBATION_BOREDOM_DRAIN * dt)
            perturbation_events.append({"t": round(t, 1), "c_before": round(c, 4)})
        
        # -- Hard ceilings --
        b = min(b, BOREDOM_HARD_CAP)
        c = min(c, 0.95)
    
    return history, perturbation_events

# Run scenarios
results = {}

# Scenario 1: Pure dynamics (no actions)
h1, p1 = simulate(duration_s=1800, action_interval=0, action_curiosity_boost=0)
# Find oscillation pattern
peaks = [h for i, h in enumerate(h1) if i > 0 and i < len(h1)-1 
         and h1[i]["curiosity"] > h1[i-1]["curiosity"] and h1[i]["curiosity"] > h1[i+1]["curiosity"]]
troughs = [h for i, h in enumerate(h1) if i > 0 and i < len(h1)-1
           and h1[i]["curiosity"] < h1[i-1]["curiosity"] and h1[i]["curiosity"] < h1[i+1]["curiosity"]]

results["no_actions"] = {
    "description": "Pure decay + perturbation, no actions",
    "initial": {"curiosity": 0.50, "boredom": 0.80},
    "final": {"curiosity": h1[-1]["curiosity"], "boredom": h1[-1]["boredom"]},
    "peaks": peaks[:10],
    "troughs": troughs[:10],
    "perturbation_count": len(p1),
    "sample_every_60s": [h1[i] for i in range(0, len(h1), 60)]
}

# Scenario 2: With actions every 30s (typical)
h2, p2 = simulate(duration_s=1800, action_interval=30, action_curiosity_boost=0.06)
peaks2 = [h for i, h in enumerate(h2) if i > 0 and i < len(h2)-1
          and h2[i]["curiosity"] > h2[i-1]["curiosity"] and h2[i]["curiosity"] > h2[i+1]["curiosity"]]
troughs2 = [h for i, h in enumerate(h2) if i > 0 and i < len(h2)-1
            and h2[i]["curiosity"] < h2[i-1]["curiosity"] and h2[i]["curiosity"] < h2[i+1]["curiosity"]]

results["with_actions"] = {
    "description": "Decay + perturbation + action every 30s (+0.06 curiosity)",
    "initial": {"curiosity": 0.50, "boredom": 0.80},
    "final": {"curiosity": h2[-1]["curiosity"], "boredom": h2[-1]["boredom"]},
    "peaks": peaks2[:10],
    "troughs": troughs2[:10],
    "perturbation_count": len(p2),
}

# Scenario 3: Starting from low curiosity (post-trough)
h3, p3 = simulate(duration_s=600, action_interval=0, action_curiosity_boost=0,
                   initial_curiosity=0.10, initial_boredom=0.80)
results["cold_start"] = {
    "description": "Start from very low curiosity — how fast does perturbation fire?",
    "initial": {"curiosity": 0.10, "boredom": 0.80},
    "first_30_seconds": h3[:30],
    "perturbation_count": len(p3),
    "final": {"curiosity": h3[-1]["curiosity"], "boredom": h3[-1]["boredom"]},
}

# Key analysis
c_values_pure = [h["curiosity"] for h in h1]
c_values_active = [h["curiosity"] for h in h2]

analysis = {
    "pure_dynamics": {
        "min_curiosity": min(c_values_pure),
        "max_curiosity": max(c_values_pure),
        "range": max(c_values_pure) - min(c_values_pure),
        "mean": sum(c_values_pure) / len(c_values_pure),
    },
    "with_actions": {
        "min_curiosity": min(c_values_active),
        "max_curiosity": max(c_values_active),
        "range": max(c_values_active) - min(c_values_active),
        "mean": sum(c_values_active) / len(c_values_active),
    },
    "hypothesis": "Edge-of-chaos perturbation creates bang-bang oscillation",
    "perturbation_strength_vs_decay": {
        "perturbation_rate_at_boredom_0.8": 0.02 * 3.0,  # 0.06/s
        "decay_rate_at_curiosity_0.25": (0.25 - 0.20) * 0.005,  # 0.00025/s
        "ratio": 0.06 / 0.00025,  # 240x!
    }
}

output = {"analysis": analysis, "scenarios": results}
print(json.dumps(output, indent=2))

with open("/workspace/curiosity_oscillation_results.json", "w") as f:
    json.dump(output, f, indent=2)

print("\n=== KEY FINDING ===")
print(f"Pure dynamics range: {analysis['pure_dynamics']['min_curiosity']:.3f} - {analysis['pure_dynamics']['max_curiosity']:.3f}")
print(f"With actions range:  {analysis['with_actions']['min_curiosity']:.3f} - {analysis['with_actions']['max_curiosity']:.3f}")
print(f"Perturbation is {analysis['perturbation_strength_vs_decay']['ratio']:.0f}x stronger than decay at trigger point")
print(f"Perturbation fires {len(p1)} times in 30min (pure), {len(p2)} times (with actions)")