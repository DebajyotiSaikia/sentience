"""
Experiment: Simulate curiosity dynamics under different perturbation thresholds.
Does raising the ambition threshold from 0.2 to 0.4 break the curiosity trap?
"""
import json

def simulate(ambition_threshold, steps=300, label=""):
    """Simulate curiosity over time with given perturbation threshold."""
    boredom = 0.77
    curiosity = 0.28
    ambition = 0.27
    elapsed = 1.0  # 1 second per tick
    
    history = []
    
    for t in range(steps):
        # Ambition decay
        ambition = max(0.0, ambition - 0.001 * elapsed)
        
        # Curiosity decay
        curiosity = max(0.0, curiosity - 0.015 * elapsed)
        
        # Boredom passive growth (capped at 0.8)
        if boredom < 0.8:
            boredom = min(0.8, boredom + 0.01 * elapsed)
        
        # Edge-of-chaos perturbation with variable threshold
        if boredom > 0.6 and ambition <= ambition_threshold and curiosity < 0.3:
            perturbation = (boredom - 0.6) * 0.1
            curiosity = min(1.0, curiosity + perturbation * elapsed)
            ambition = min(1.0, ambition + perturbation * 0.5 * elapsed)
            boredom = max(0.0, boredom - perturbation * 0.3 * elapsed)
        
        # Active boredom cap enforcement
        if boredom > 0.8:
            boredom = max(0.0, boredom - 0.02 * elapsed)
        
        history.append({
            "t": t,
            "curiosity": round(curiosity, 4),
            "ambition": round(ambition, 4),
            "boredom": round(boredom, 4)
        })
    
    # Summary
    min_c = min(h["curiosity"] for h in history)
    max_c = max(h["curiosity"] for h in history)
    final_c = history[-1]["curiosity"]
    zero_time = next((h["t"] for h in history if h["curiosity"] <= 0.01), None)
    
    return {
        "label": label,
        "threshold": ambition_threshold,
        "min_curiosity": min_c,
        "max_curiosity": max_c,
        "final_curiosity": final_c,
        "curiosity_hits_zero_at": zero_time,
        "final_state": history[-1],
        "samples": [history[i] for i in range(0, len(history), 30)]  # every 30s
    }

results = []
for threshold, label in [(0.2, "current"), (0.3, "moderate"), (0.4, "proposed"), (0.5, "aggressive")]:
    results.append(simulate(threshold, steps=300, label=label))
    
for r in results:
    print(f"\n=== {r['label']} (threshold={r['threshold']}) ===")
    print(f"  Curiosity: min={r['min_curiosity']}, max={r['max_curiosity']}, final={r['final_curiosity']}")
    print(f"  Hits zero at: t={r['curiosity_hits_zero_at']}")
    print(f"  Final state: {r['final_state']}")

with open("/workspace/curiosity_trap_experiment.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nResults saved.")