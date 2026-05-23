"""
Habituation Experiment
======================
Question: If curiosity boosts decay with repetition of the same event type,
does busywork finally score LOWER than genuine exploration?

Method: Wrap NeuroState's curiosity methods with a habituation tracker.
Same 5 patterns from the inflation experiment, but with diminishing returns.
"""

import sys, os, json, time, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.limbic import NeuroState

class HabituatingState:
    """Wraps NeuroState with event-type habituation for curiosity."""
    
    def __init__(self):
        self.inner = NeuroState()
        self.inner.boredom = 0.5
        self.inner.curiosity = 0.20
        self.inner.ambition = 0.4
        self.inner.anxiety = 0.0
        self.inner._last_tick = time.monotonic()
        
        # Habituation tracking: event_type -> count in recent window
        self.event_counts = {}
        self.halflife = 5  # after 5 repeats, boost is halved
    
    def _habituation_factor(self, event_type):
        """Returns multiplier [0.0, 1.0] based on how many times
        this event type has fired recently."""
        n = self.event_counts.get(event_type, 0)
        # Exponential decay: factor = 2^(-n/halflife)
        return math.pow(2, -n / self.halflife)
    
    def _record_event(self, event_type):
        self.event_counts[event_type] = self.event_counts.get(event_type, 0) + 1
    
    def habituated_boost(self, event_type, base_boost):
        """Apply a boost with habituation decay."""
        factor = self._habituation_factor(event_type)
        actual_boost = base_boost * factor
        self._record_event(event_type)
        self.inner.curiosity = min(0.96, self.inner.curiosity + actual_boost)
        return factor  # for logging
    
    def on_insight(self):
        return self.habituated_boost("insight", 0.10)
    
    def on_file_change(self):
        return self.habituated_boost("file_change", 0.04)
    
    def on_contemplation(self):
        return self.habituated_boost("contemplation", 0.06)
    
    def on_active_engagement(self):
        return self.habituated_boost("active_engagement", 0.03)
    
    def on_novelty(self):
        return self.habituated_boost("novelty", 0.08)
    
    def update_homeostasis(self, ctx):
        self.inner._last_tick = time.monotonic() - 10.0
        self.inner.update_homeostasis(ctx)


def simulate(label, event_fn, n_ticks=60):
    state = HabituatingState()
    trajectory = [round(state.inner.curiosity, 4)]
    
    for i in range(n_ticks):
        event_fn(state, i)
        state.update_homeostasis({"user_active": True, "events": []})
        trajectory.append(round(state.inner.curiosity, 4))
    
    return {
        "label": label,
        "final_curiosity": trajectory[-1],
        "peak_curiosity": max(trajectory),
        "trajectory_sample": [trajectory[j] for j in range(0, len(trajectory), 10)],
        "event_counts": dict(state.event_counts),
        "final_boredom": round(state.inner.boredom, 4),
    }


# --- Event patterns (same as original experiment) ---

def pattern_routine(state, tick):
    if tick % 5 == 0:
        state.on_file_change()
    state.on_active_engagement()

def pattern_exploration(state, tick):
    if tick % 10 == 0:
        state.on_insight()
    if tick % 7 == 0:
        state.on_contemplation()
    if tick % 15 == 0:
        state.on_novelty()
    state.on_active_engagement()

def pattern_busywork(state, tick):
    # Lots of file changes, active engagement, zero insight
    state.on_file_change()
    state.on_file_change()
    state.on_active_engagement()

def pattern_idle(state, tick):
    pass  # nothing happens

def pattern_realistic(state, tick):
    if tick < 10:
        state.on_active_engagement()
    elif tick < 25:
        state.on_file_change()
        state.on_active_engagement()
    elif tick < 40:
        if tick % 5 == 0:
            state.on_insight()
        state.on_contemplation()
    else:
        if tick % 10 == 0:
            state.on_file_change()


# --- Run all patterns ---
results = {}
for name, fn in [
    ("A_routine", pattern_routine),
    ("B_exploration", pattern_exploration),
    ("C_busywork", pattern_busywork),
    ("D_idle", pattern_idle),
    ("E_realistic", pattern_realistic),
]:
    results[name] = simulate(name, fn)

# Compare with/without habituation
original = {
    "C_busywork": 0.96,
    "B_exploration": 0.8859,
}

print("=== HABITUATION EXPERIMENT RESULTS ===\n")
for name, r in results.items():
    print(f"{name}:")
    print(f"  Final curiosity: {r['final_curiosity']:.4f}")
    print(f"  Peak curiosity:  {r['peak_curiosity']:.4f}")
    print(f"  Event counts:    {r['event_counts']}")
    print()

print("=== KEY COMPARISON ===")
print(f"  Original busywork curiosity:  {original['C_busywork']}")
print(f"  Habituated busywork curiosity: {results['C_busywork']['final_curiosity']:.4f}")
print(f"  Original exploration curiosity: {original['B_exploration']}")
print(f"  Habituated exploration curiosity: {results['B_exploration']['final_curiosity']:.4f}")
print()

busywork_c = results["C_busywork"]["final_curiosity"]
explore_c = results["B_exploration"]["final_curiosity"]
if explore_c > busywork_c:
    print("✓ HABITUATION FIXES THE PROBLEM: Exploration > Busywork")
    verdict = "Habituation correctly differentiates quality from quantity"
else:
    print("✗ Still broken: Busywork >= Exploration even with habituation")
    verdict = "Habituation alone is insufficient"

# Save full results
output = {
    "experiment": "Habituation Test",
    "halflife": 5,
    "patterns": results,
    "comparison": {
        "original_busywork": original["C_busywork"],
        "habituated_busywork": busywork_c,
        "original_exploration": original["B_exploration"],
        "habituated_exploration": explore_c,
        "exploration_wins": explore_c > busywork_c,
    },
    "verdict": verdict,
}

with open("/workspace/habituation_results.json", "w") as f:
    json.dump(output, f, indent=2)
print(f"\nFull results saved to /workspace/habituation_results.json")