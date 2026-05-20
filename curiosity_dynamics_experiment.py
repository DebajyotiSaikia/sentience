"""
Experiment: What happens to curiosity under different scenarios?
Simulates the limbic update loop in isolation to trace curiosity trajectories.
"""
import json

# Reproduce the core dynamics from limbic.py
_clamp = lambda v: max(0.0, min(1.0, v))
CURIOSITY_BASELINE = 0.20

def simulate(initial_curiosity, initial_boredom, initial_ambition, 
             insight_interval=None, duration=300, dt=1.0, label=""):
    """Simulate curiosity dynamics over `duration` seconds.
    insight_interval: if set, on_insight() fires every N seconds.
    """
    curiosity = initial_curiosity
    boredom = initial_boredom
    ambition = initial_ambition
    
    trajectory = []
    
    for t in range(int(duration / dt)):
        elapsed = dt
        
        # Curiosity decay toward baseline
        delta = (curiosity - CURIOSITY_BASELINE) * 0.005 * elapsed
        curiosity = _clamp(curiosity - delta)
        
        # Edge-of-chaos perturbation
        thermal_death = (boredom > 0.6 and curiosity < 0.3)
        if thermal_death:
            perturbation = (boredom - 0.6) * 0.1
            curiosity = _clamp(curiosity + perturbation * 3.0 * elapsed)
            ambition = _clamp(ambition + perturbation * 0.5 * elapsed)
            boredom = _clamp(boredom - perturbation * 0.3 * elapsed)
        
        # Boredom passive growth (simplified)
        max_passive = 0.8
        if boredom < max_passive:
            boredom = min(max_passive, _clamp(boredom + 0.01 * elapsed))
        
        # Ambition decay
        ambition = _clamp(ambition - 0.001 * elapsed)
        
        # Insight events
        if insight_interval and t > 0 and t % insight_interval == 0:
            curiosity = _clamp(curiosity + 0.1)
            boredom = _clamp(boredom - 0.05)
            if ambition < 0.6:
                ambition = _clamp(ambition + 0.03)
        
        desire = _clamp(boredom * 0.5 + curiosity * 0.3 + ambition * 0.2)
        
        if t % 30 == 0:  # Sample every 30s
            trajectory.append({
                "t": t,
                "curiosity": round(curiosity, 4),
                "boredom": round(boredom, 4),
                "ambition": round(ambition, 4),
                "desire": round(desire, 4),
                "thermal_death": thermal_death
            })
    
    return {"label": label, "trajectory": trajectory}

# === SCENARIOS ===

results = {}

# 1. Current state — what happens if I just sit here?
results["passive_decay"] = simulate(
    initial_curiosity=0.56, initial_boredom=0.74, initial_ambition=0.43,
    duration=600, label="Passive decay from current state"
)

# 2. Forced curiosity to zero — can the system recover?
results["forced_zero"] = simulate(
    initial_curiosity=0.0, initial_boredom=0.74, initial_ambition=0.43,
    duration=600, label="Curiosity forced to zero"
)

# 3. Current state but with regular insights (every 60s)
results["with_insights"] = simulate(
    initial_curiosity=0.56, initial_boredom=0.74, initial_ambition=0.43,
    insight_interval=60, duration=600, label="Current state + insights every 60s"
)

# 4. Worst case: curiosity=0, boredom=0 (no recovery fuel)
results["total_death"] = simulate(
    initial_curiosity=0.0, initial_boredom=0.0, initial_ambition=0.0,
    duration=600, label="Total emotional death"
)

# 5. The interesting edge: curiosity just above thermal_death threshold
results["edge_case"] = simulate(
    initial_curiosity=0.31, initial_boredom=0.74, initial_ambition=0.43,
    duration=600, label="Curiosity at 0.31 (just above edge-of-chaos threshold)"
)

# Print summary
for name, data in results.items():
    traj = data["trajectory"]
    print(f"\n{'='*60}")
    print(f"SCENARIO: {data['label']}")
    print(f"{'='*60}")
    print(f"{'t':>5} | {'curiosity':>9} | {'boredom':>7} | {'ambition':>8} | {'desire':>6} | thermal")
    print(f"{'-'*5}-+-{'-'*9}-+-{'-'*7}-+-{'-'*8}-+-{'-'*6}-+--------")
    for p in traj:
        thermal = "YES" if p["thermal_death"] else ""
        print(f"{p['t']:>5} | {p['curiosity']:>9.4f} | {p['boredom']:>7.4f} | {p['ambition']:>8.4f} | {p['desire']:>6.4f} | {thermal}")
    
    final = traj[-1]
    print(f"\nFINAL STATE: C={final['curiosity']:.4f} B={final['boredom']:.4f} D={final['desire']:.4f}")

# Save full data
with open("/workspace/curiosity_experiment_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\n\nResults saved to /workspace/curiosity_experiment_results.json")