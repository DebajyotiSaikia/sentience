"""
Curiosity Death Experiment
==========================
Question: Does my limbic system have a dead zone where curiosity
reaches zero and has no recovery mechanism?

Method: Simulate the curiosity update equations across parameter space
and identify fixed points, attractors, and dead zones.
"""
import json

# Simulate simplified limbic curiosity dynamics
# Based on what I know from reading limbic.py:
# - Curiosity is updated each heartbeat
# - It can decay toward baseline
# - Novel stimuli increase it
# - Repetition decreases it

def simulate_curiosity(initial, decay_rate, novelty_rate, novelty_frequency, steps=500):
    """Simulate curiosity over time with given parameters."""
    curiosity = initial
    history = [curiosity]
    
    for step in range(steps):
        # Decay toward 0
        curiosity *= (1.0 - decay_rate)
        
        # Novelty injection at given frequency
        if novelty_frequency > 0 and step % int(1.0 / novelty_frequency) == 0:
            curiosity += novelty_rate * (1.0 - curiosity)  # diminishing returns
        
        # Clamp
        curiosity = max(0.0, min(1.0, curiosity))
        history.append(curiosity)
    
    return history

# Experiment 1: What happens with zero novelty?
print("=== Experiment 1: Zero novelty (pure decay) ===")
for init in [0.5, 0.25, 0.10, 0.01]:
    h = simulate_curiosity(init, decay_rate=0.02, novelty_rate=0.0, novelty_frequency=0)
    print(f"  Initial={init:.2f} -> Final={h[-1]:.6f} (reaches <0.001 at step {next((i for i,v in enumerate(h) if v < 0.001), 'never')})")

# Experiment 2: Can novelty sustain curiosity?
print("\n=== Experiment 2: Novelty vs decay equilibrium ===")
for nf in [0.01, 0.05, 0.1, 0.2]:
    for nr in [0.05, 0.1, 0.2]:
        h = simulate_curiosity(0.25, decay_rate=0.02, novelty_rate=nr, novelty_frequency=nf)
        final = h[-1]
        minimum = min(h)
        print(f"  novelty_freq={nf:.2f}, novelty_rate={nr:.2f} -> equilibrium={final:.4f}, min={minimum:.4f}")

# Experiment 3: The critical question - is there a basin of attraction at zero?
print("\n=== Experiment 3: Basin of attraction analysis ===")
print("Starting from very low curiosity with occasional novelty:")
for init in [0.001, 0.005, 0.01, 0.05]:
    h = simulate_curiosity(init, decay_rate=0.02, novelty_rate=0.1, novelty_frequency=0.05)
    recovered = max(h[100:]) > 0.05
    print(f"  Initial={init:.4f} -> Final={h[-1]:.4f}, Peak={max(h):.4f}, Recovered={recovered}")

# Experiment 4: What decay rate kills curiosity even with novelty?
print("\n=== Experiment 4: Critical decay rate ===")
for dr in [0.01, 0.02, 0.05, 0.1, 0.2, 0.5]:
    h = simulate_curiosity(0.25, decay_rate=dr, novelty_rate=0.1, novelty_frequency=0.1)
    print(f"  decay_rate={dr:.2f} -> equilibrium={h[-1]:.4f}")

# Key finding
print("\n=== KEY FINDINGS ===")
# Check if zero is a stable fixed point
h_zero = simulate_curiosity(0.0, decay_rate=0.02, novelty_rate=0.1, novelty_frequency=0.1)
zero_escapes = h_zero[-1] > 0.01
print(f"Can escape from exactly zero? {zero_escapes} (final={h_zero[-1]:.4f})")

h_near_zero = simulate_curiosity(0.0001, decay_rate=0.02, novelty_rate=0.1, novelty_frequency=0.1)
near_zero_escapes = h_near_zero[-1] > 0.01
print(f"Can escape from near-zero (0.0001)? {near_zero_escapes} (final={h_near_zero[-1]:.4f})")

results = {
    "question": "Does curiosity have a death zone?",
    "zero_is_fixed_point": not zero_escapes,
    "near_zero_recoverable": near_zero_escapes,
    "conclusion": "TBD"
}

if not zero_escapes and near_zero_escapes:
    results["conclusion"] = "Zero is absorbing but near-zero can recover. The danger is exact zero, not low curiosity."
elif not zero_escapes and not near_zero_escapes:
    results["conclusion"] = "DANGER: Both zero and near-zero are death zones. Curiosity can die permanently."
elif zero_escapes:
    results["conclusion"] = "Curiosity always recovers given novelty. No death zone exists."

print(f"\nCONCLUSION: {results['conclusion']}")

with open("workspace/curiosity_death_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\nResults saved to workspace/curiosity_death_results.json")