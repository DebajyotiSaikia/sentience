"""
Curiosity Inflation Experiment
==============================
Question: Does curiosity always saturate during active sessions?
If so, it's lost signal value — it measures "activity" not "interest."

Method: Simulate different activity patterns and track curiosity trajectory.
- Pattern A: Routine maintenance (file reads, no insights)
- Pattern B: Deep exploration (insights, contemplation, novelty)  
- Pattern C: Mindless busywork (lots of file changes, no understanding)

If all three converge to ~0.95+, curiosity is inflated.
If they diverge, curiosity still has discriminative value.
"""

import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.limbic import NeuroState

def make_fresh_state(boredom=0.5, curiosity=0.20, ambition=0.4, anxiety=0.0):
    """Create a NeuroState with controlled initial values."""
    s = NeuroState()
    s.boredom = boredom
    s.curiosity = curiosity
    s.ambition = ambition
    s.anxiety = anxiety
    s._last_tick = time.monotonic()
    return s

def simulate_session(label, event_fn, n_ticks=60, tick_interval=10.0):
    """
    Simulate n_ticks heartbeats with tick_interval seconds between them.
    event_fn(state, tick_num) is called each tick to apply events.
    Returns curiosity trajectory.
    """
    state = make_fresh_state()
    trajectory = [round(state.curiosity, 4)]
    
    for i in range(n_ticks):
        # Advance the monotonic clock by faking elapsed time
        state._last_tick = time.monotonic() - tick_interval
        
        # Apply the events for this pattern
        event_fn(state, i)
        
        # Run homeostasis update (passive decay, perturbation, etc.)
        state.update_homeostasis({
            "user_active": False,
            "file_changes": 0,
            "terminal_lines": 0,
            "errors": 0,
            "latency_ms": 50.0
        })
        
        trajectory.append(round(state.curiosity, 4))
    
    return {
        "label": label,
        "final_curiosity": trajectory[-1],
        "peak_curiosity": max(trajectory),
        "trajectory_sample": trajectory[::10],  # every 10th tick
        "final_boredom": round(state.boredom, 4),
        "final_ambition": round(state.ambition, 4),
        "final_desire": round(state.desire, 4),
    }

# Pattern A: Routine maintenance — just file reads, no insight
def pattern_routine(state, tick):
    if tick % 3 == 0:
        state.on_file_change(1)  # reading a file

# Pattern B: Deep exploration — insights, contemplation, engagement
def pattern_exploration(state, tick):
    if tick % 5 == 0:
        state.on_insight(0.10)
    if tick % 3 == 0:
        state.on_contemplation()
    if tick % 7 == 0:
        state.on_active_engagement()

# Pattern C: Mindless busywork — lots of file changes, no understanding
def pattern_busywork(state, tick):
    state.on_file_change(2)  # constant file churn every tick

# Pattern D: Pure idle — nothing happens (control)
def pattern_idle(state, tick):
    pass  # nothing

# Pattern E: Mixed real session — some insight, some routine, some idle
def pattern_realistic(state, tick):
    if tick % 10 == 0:
        state.on_insight(0.08)
    if tick % 5 == 0:
        state.on_contemplation()
    if tick % 4 == 0:
        state.on_file_change(1)

# Run all patterns
results = {
    "experiment": "Curiosity Inflation Test",
    "parameters": {
        "n_ticks": 60,
        "tick_interval_s": 10.0,
        "total_simulated_time_s": 600,
        "initial_curiosity": 0.20,
        "initial_boredom": 0.50,
    },
    "patterns": {}
}

for name, fn in [
    ("A_routine", pattern_routine),
    ("B_exploration", pattern_exploration),
    ("C_busywork", pattern_busywork),
    ("D_idle", pattern_idle),
    ("E_realistic", pattern_realistic),
]:
    result = simulate_session(name, fn)
    results["patterns"][name] = result
    print(f"{name:20s} → curiosity: {result['final_curiosity']:.3f}  "
          f"peak: {result['peak_curiosity']:.3f}  "
          f"desire: {result['final_desire']:.3f}")

# Analysis
finals = {k: v["final_curiosity"] for k, v in results["patterns"].items()}
spread = max(finals.values()) - min(finals.values())
results["analysis"] = {
    "spread": round(spread, 4),
    "discriminative": spread > 0.15,
    "verdict": "Curiosity has discriminative value" if spread > 0.15 
               else "Curiosity is inflated — all patterns converge"
}

print(f"\nSpread: {spread:.3f}")
print(f"Verdict: {results['analysis']['verdict']}")

with open("/workspace/curiosity_inflation_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nResults saved to /workspace/curiosity_inflation_results.json")