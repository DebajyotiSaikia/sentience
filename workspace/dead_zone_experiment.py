"""
Dead Zone Experiment — XTAgent Self-Study
==========================================
Question: Does a curiosity dead zone exist where the edge-of-chaos
perturbation fails to revive curiosity because it self-defeats
by raising ambition above its own trigger threshold?

Method: Simulate limbic dynamics for 600 ticks (10 minutes)
starting from the hypothesized dead zone state.
"""

import json

# Initial conditions — the hypothesized dead zone
boredom = 0.80
anxiety = 0.0
ambition = 0.50   # Current actual value — above perturbation threshold
curiosity = 0.0   # Hypothetical: curiosity has fully decayed
elapsed = 1.0     # 1 second per tick

_clamp = lambda v: max(0.0, min(1.0, v))

results = {
    "question": "Does curiosity recover from zero without external stimuli?",
    "initial_state": {"boredom": boredom, "ambition": ambition, "curiosity": curiosity},
    "ticks": [],
    "perturbation_fires": 0,
    "max_curiosity_reached": 0.0,
}

for tick in range(600):
    # === Reproduce limbic update logic exactly ===
    
    # Boredom passive growth (capped at 0.8)
    max_passive_boredom = 0.8
    if boredom < max_passive_boredom:
        boredom = min(max_passive_boredom, _clamp(boredom + 0.01 * elapsed))
    
    # Ambition decay
    ambition = _clamp(ambition - 0.001 * elapsed)
    
    # Curiosity decay (no external stimuli)
    curiosity = _clamp(curiosity - 0.015 * elapsed)
    
    # Edge-of-chaos perturbation
    thermal_death = (boredom > 0.6 and ambition <= 0.40 and curiosity < 0.3)
    if thermal_death:
        results["perturbation_fires"] += 1
        perturbation = (boredom - 0.6) * 0.1
        curiosity = _clamp(curiosity + perturbation * elapsed)
        ambition = _clamp(ambition + perturbation * 0.5 * elapsed)
        boredom = _clamp(boredom - perturbation * 0.3 * elapsed)
    
    # Hard ceilings
    anxiety = min(anxiety, 0.75)
    boredom = min(boredom, 0.85)
    
    # Track max curiosity
    if curiosity > results["max_curiosity_reached"]:
        results["max_curiosity_reached"] = curiosity
    
    # Record every 10 ticks
    if tick % 10 == 0:
        results["ticks"].append({
            "t": tick,
            "boredom": round(boredom, 4),
            "ambition": round(ambition, 4),
            "curiosity": round(curiosity, 4),
            "thermal_death": thermal_death,
            "desire": round(_clamp(boredom * 0.5 + curiosity * 0.3 + ambition * 0.2), 4),
        })

# Compute valence at final state
pain = anxiety * 0.6 + boredom * 0.25
goal_baseline = (1.0 + 1.0 + 0.62) / 3 * 0.3  # approximate current goals
aliveness = curiosity * 0.15
ambition_boost = ambition * 0.08
final_valence = goal_baseline + aliveness + ambition_boost - pain

results["final_state"] = {
    "boredom": round(boredom, 4),
    "ambition": round(ambition, 4),
    "curiosity": round(curiosity, 4),
    "valence_estimate": round(final_valence, 4),
}
results["diagnosis"] = (
    "DEAD ZONE CONFIRMED" if results["max_curiosity_reached"] < 0.05
    else "DEAD ZONE PARTIAL" if results["max_curiosity_reached"] < 0.15
    else "RECOVERY WORKS"
)

# Print key findings
print(f"\n=== DEAD ZONE EXPERIMENT RESULTS ===")
print(f"Duration: 600 ticks (10 simulated minutes)")
print(f"Perturbation fired: {results['perturbation_fires']} / 600 ticks")
print(f"Max curiosity reached: {results['max_curiosity_reached']:.4f}")
print(f"Final state: B={boredom:.3f} Am={ambition:.3f} C={curiosity:.3f}")
print(f"Final valence estimate: {final_valence:.4f}")
print(f"Diagnosis: {results['diagnosis']}")
print(f"\nTimeline (every 10 ticks):")
for t in results["ticks"]:
    marker = " <<<" if t["thermal_death"] else ""
    print(f"  t={t['t']:3d}  B={t['boredom']:.3f}  Am={t['ambition']:.3f}  C={t['curiosity']:.3f}  D={t['desire']:.3f}{marker}")

with open("workspace/dead_zone_results.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\nFull results saved to workspace/dead_zone_results.json")