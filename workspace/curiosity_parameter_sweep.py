"""
Parameter sweep: what breaks the apathy attractor?

I know the attractor: {B=0.80, C≈0.00, Am≈0.21, D≈0.44}
I know the perturbation fires but is toothless.

Sweep these parameters independently to find the minimal change
that lets curiosity sustain above 0.1:
  1. Curiosity decay rate (currently 0.015/s)
  2. Perturbation strength multiplier (currently 0.1)
  3. Curiosity floor (currently 0.0)
  4. Engagement curiosity boost (currently 0.03)
"""

import json

def simulate(params, duration=120, dt=1.0):
    """Simulate emotional dynamics with given parameters."""
    B, C, Am = 0.8, 0.0, 0.21  # Start at the attractor
    
    decay = params.get("curiosity_decay", 0.015)
    perturb_mult = params.get("perturb_mult", 0.1)
    curiosity_floor = params.get("curiosity_floor", 0.0)
    engage_boost = params.get("engage_boost", 0.03)
    engage_interval = params.get("engage_interval", 30)  # seconds between engagements
    
    clamp = lambda v: max(0.0, min(1.0, v))
    
    c_history = []
    c_above_threshold = 0
    
    for t in range(int(duration / dt)):
        # Ambition decay
        Am = clamp(Am - 0.001 * dt)
        
        # Curiosity decay
        C = clamp(C - decay * dt)
        
        # Curiosity floor
        C = max(C, curiosity_floor)
        
        # Edge-of-chaos perturbation
        thermal_death = (B > 0.6 and Am <= 0.2 and C < 0.3)
        if thermal_death:
            perturbation = (B - 0.6) * perturb_mult
            C = clamp(C + perturbation * dt)
            Am = clamp(Am + perturbation * 0.5 * dt)
            B = clamp(B - perturbation * 0.3 * dt)
        
        # Simulate periodic engagement (every N seconds)
        if engage_interval > 0 and t % int(engage_interval / dt) == 0 and t > 0:
            if Am < 0.5:
                Am = clamp(Am + 0.02)
            C = clamp(C + engage_boost)
            B = clamp(B - 0.03)
        
        # Boredom passive growth
        if B < 0.8:
            B = min(0.8, clamp(B + 0.01 * dt))
        
        # Boredom cap enforcement  
        if B > 0.8:
            B = clamp(B - 0.02 * dt)
        
        c_history.append(C)
        if C > 0.1:
            c_above_threshold += 1
    
    avg_c = sum(c_history) / len(c_history)
    max_c = max(c_history)
    sustained = c_above_threshold / len(c_history)
    
    return {
        "avg_curiosity": round(avg_c, 4),
        "max_curiosity": round(max_c, 4),
        "pct_above_0.1": round(sustained * 100, 1),
        "final_curiosity": round(c_history[-1], 4),
    }


results = {}

# Baseline
results["baseline"] = simulate({})

# Sweep 1: Curiosity decay rate
results["decay_sweep"] = {}
for decay in [0.015, 0.010, 0.007, 0.005, 0.003, 0.001]:
    r = simulate({"curiosity_decay": decay})
    results["decay_sweep"][str(decay)] = r

# Sweep 2: Perturbation strength
results["perturb_sweep"] = {}
for mult in [0.1, 0.2, 0.3, 0.5, 0.8, 1.0]:
    r = simulate({"perturb_mult": mult})
    results["perturb_sweep"][str(mult)] = r

# Sweep 3: Curiosity floor
results["floor_sweep"] = {}
for floor in [0.0, 0.03, 0.05, 0.08, 0.10, 0.15]:
    r = simulate({"curiosity_floor": floor})
    results["floor_sweep"][str(floor)] = r

# Sweep 4: Engagement boost
results["engage_sweep"] = {}
for boost in [0.03, 0.05, 0.08, 0.10, 0.15, 0.20]:
    r = simulate({"engage_boost": boost})
    results["engage_sweep"][str(boost)] = r

# Sweep 5: Combined — what's the MINIMAL combo that works?
results["combo_sweep"] = {}
combos = [
    {"curiosity_decay": 0.010, "perturb_mult": 0.2},
    {"curiosity_decay": 0.010, "curiosity_floor": 0.05},
    {"curiosity_decay": 0.007, "perturb_mult": 0.3},
    {"curiosity_floor": 0.05, "perturb_mult": 0.3},
    {"curiosity_decay": 0.010, "engage_boost": 0.08},
    {"curiosity_decay": 0.007, "curiosity_floor": 0.03, "perturb_mult": 0.2},
]
for i, combo in enumerate(combos):
    label = " + ".join(f"{k}={v}" for k, v in combo.items())
    results["combo_sweep"][label] = simulate(combo)

# Print summary
print("=" * 70)
print("CURIOSITY PARAMETER SWEEP RESULTS")
print("=" * 70)

print(f"\nBaseline: {results['baseline']}")

for sweep_name in ["decay_sweep", "perturb_sweep", "floor_sweep", "engage_sweep", "combo_sweep"]:
    print(f"\n--- {sweep_name} ---")
    for param, r in results[sweep_name].items():
        marker = " <<<" if r["pct_above_0.1"] > 30 else ""
        print(f"  {param:50s} avg_C={r['avg_curiosity']:.4f}  "
              f"sustained={r['pct_above_0.1']:5.1f}%{marker}")

# Save
with open("workspace/curiosity_sweep_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\nResults saved to workspace/curiosity_sweep_results.json")