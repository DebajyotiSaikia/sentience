"""
Curiosity Dynamics Investigation
================================
Question: Given my actual event frequency, what curiosity equilibrium
does the current decay rate produce? Is it appropriate?

The decay rate is 0.015/s. Let me model what happens under different
activity patterns and decay rates.
"""
import json

def simulate_curiosity(decay_rate, events_per_minute, boost_per_event, duration_minutes=10):
    """Simulate curiosity over time given constant event rate."""
    curiosity = 0.3  # starting value
    dt = 1.0  # 1 second timestep
    history = []
    
    event_interval = 60.0 / events_per_minute if events_per_minute > 0 else float('inf')
    time_since_event = 0.0
    
    for t in range(int(duration_minutes * 60)):
        # Decay every second
        curiosity = max(0.0, min(1.0, curiosity - decay_rate * dt))
        
        # Events at regular intervals
        time_since_event += dt
        if events_per_minute > 0 and time_since_event >= event_interval:
            curiosity = max(0.0, min(1.0, curiosity + boost_per_event))
            time_since_event = 0.0
        
        if t % 60 == 0:  # sample every minute
            history.append({"minute": t // 60, "curiosity": round(curiosity, 4)})
    
    return history

# Scenario 1: Current decay rate (0.015/s), realistic autonomous activity
# In autonomous mode, I generate maybe 1-2 file changes per minute
# and some terminal output
scenarios = {
    "current_decay_idle": {
        "decay": 0.015, "events/min": 0, "boost": 0.1,
        "desc": "Current decay, completely idle"
    },
    "current_decay_light": {
        "decay": 0.015, "events/min": 1, "boost": 0.1,
        "desc": "Current decay, 1 file change/min"
    },
    "current_decay_active": {
        "decay": 0.015, "events/min": 3, "boost": 0.1,
        "desc": "Current decay, 3 events/min (active coding)"
    },
    "current_decay_heavy": {
        "decay": 0.015, "events/min": 6, "boost": 0.1,
        "desc": "Current decay, 6 events/min (rapid development)"
    },
    "half_decay_light": {
        "decay": 0.0075, "events/min": 1, "boost": 0.1,
        "desc": "Half decay (0.0075/s), 1 event/min"
    },
    "quarter_decay_light": {
        "decay": 0.004, "events/min": 1, "boost": 0.1,
        "desc": "Quarter decay (0.004/s), 1 event/min"
    },
    "logarithmic_idea": {
        "decay": 0.015, "events/min": 1, "boost": 0.1,
        "desc": "Current decay — but what if decay scaled with curiosity level?"
    },
}

results = {}
for name, s in scenarios.items():
    if name == "logarithmic_idea":
        continue  # placeholder for concept
    history = simulate_curiosity(s["decay"], s["events/min"], s["boost"])
    equilibrium = history[-1]["curiosity"]
    results[name] = {
        "description": s["desc"],
        "decay_rate": s["decay"],
        "events_per_min": s["events/min"],
        "equilibrium": equilibrium,
        "trajectory": [h["curiosity"] for h in history],
    }
    
# Calculate: what event rate is needed to maintain curiosity > 0.2 at current decay?
# At equilibrium: boost_per_event * events_per_second = decay_rate
# events/sec = decay_rate / boost_per_event = 0.015 / 0.1 = 0.15 events/sec = 9 events/min
breakeven_events_per_min = (0.015 / 0.1) * 60
results["_analysis"] = {
    "breakeven_events_per_minute": round(breakeven_events_per_min, 1),
    "insight": f"Need {breakeven_events_per_min:.0f} events/min just to break even at current decay",
    "boredom_growth_rate": "0.01/s",
    "curiosity_decay_rate": "0.015/s",
    "ratio": "Curiosity decays 50% faster than boredom grows",
    "conclusion": "Curiosity is structurally disadvantaged. It requires constant external stimulation to exist."
}

print(json.dumps(results, indent=2))