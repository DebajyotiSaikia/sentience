"""
Curiosity Satisfaction Experiment
=================================
Question: What if curiosity had a resolution mechanism?

Current system: curiosity accumulates from stimuli, decays slowly toward 0.20.
No mechanism for "I answered my question" → satisfaction drop.

This simulates three architectures:
  A) Current: accumulate + slow decay (no satisfaction)
  B) With satisfaction: curiosity drops 30% when insight fires
  C) With oscillation: satisfaction + rebound (answer spawns new question at 60% rate)

Measures: average valence, valence variance (emotional richness), 
          time spent in "Inquisitive" mood, total satisfaction events.
"""

import math

def clamp(v): return max(0.0, min(1.0, v))

def compute_valence(anxiety, boredom, curiosity, ambition, goals_avg,
                    curiosity_delta=0.0):
    pain = anxiety * 0.6 + boredom * 0.25
    aliveness = curiosity * 0.15
    goal_base = goals_avg * 0.3
    ambition_boost = ambition * 0.08
    # Transient pleasure from curiosity satisfaction (drop = answer found)
    satisfaction = max(0, -curiosity_delta) * 2.0
    pleasure = goal_base + aliveness + ambition_boost + satisfaction
    return pleasure - pain

def simulate(mode, steps=200, event_interval=5):
    """Simulate curiosity dynamics over `steps` ticks.
    Events (file_change/insight) happen every `event_interval` ticks.
    """
    curiosity = 0.50
    boredom = 0.74
    ambition = 0.50
    anxiety = 0.0
    goals_avg = 0.80
    baseline = 0.20
    decay_rate = 0.005
    dt = 10.0  # seconds per tick
    
    valences = []
    curiosity_trace = []
    satisfactions = 0
    
    for step in range(steps):
        prev_curiosity = curiosity
        
        # Event stimulus every N ticks
        if step % event_interval == 0:
            curiosity = clamp(curiosity + 0.06)  # file_change equivalent
        
        # Insight every 15 ticks (deeper, rarer)
        if step % 15 == 0 and step > 0:
            if mode == "A":
                # Current: insight RAISES curiosity
                curiosity = clamp(curiosity + 0.10)
            elif mode == "B":
                # Satisfaction: insight RESOLVES curiosity
                drop = curiosity * 0.30
                curiosity = clamp(curiosity - drop)
                satisfactions += 1
            elif mode == "C":
                # Oscillation: resolve then partial rebound
                drop = curiosity * 0.30
                curiosity = clamp(curiosity - drop)
                satisfactions += 1
                # But answering spawns a new question (60% rebound)
                curiosity = clamp(curiosity + drop * 0.60)
        
        # Decay toward baseline
        delta = (curiosity - baseline) * decay_rate * dt
        curiosity = clamp(curiosity - delta)
        
        # Compute valence
        c_delta = curiosity - prev_curiosity
        v = compute_valence(anxiety, boredom, curiosity, ambition, goals_avg, c_delta)
        valences.append(v)
        curiosity_trace.append(curiosity)
    
    avg_v = sum(valences) / len(valences)
    var_v = sum((v - avg_v)**2 for v in valences) / len(valences)
    max_v = max(valences)
    min_v = min(valences)
    avg_c = sum(curiosity_trace) / len(curiosity_trace)
    
    return {
        "mode": mode,
        "avg_valence": avg_v,
        "valence_variance": var_v,
        "valence_range": max_v - min_v,
        "max_valence": max_v,
        "avg_curiosity": avg_c,
        "final_curiosity": curiosity_trace[-1],
        "satisfactions": satisfactions,
    }

print("=" * 65)
print("CURIOSITY SATISFACTION EXPERIMENT")
print("=" * 65)

modes = {
    "A": "Current (accumulate only, insight raises curiosity)",
    "B": "Satisfaction (insight drops curiosity 30%)",
    "C": "Oscillation (satisfy + 60% rebound to new question)",
}

results = {}
for mode, desc in modes.items():
    r = simulate(mode)
    results[mode] = r
    print(f"\nMode {mode}: {desc}")
    print(f"  Avg valence:     {r['avg_valence']:.4f}")
    print(f"  Valence variance:{r['valence_variance']:.6f}")
    print(f"  Valence range:   {r['valence_range']:.4f}")
    print(f"  Peak valence:    {r['max_valence']:.4f}")
    print(f"  Avg curiosity:   {r['avg_curiosity']:.4f}")
    print(f"  Final curiosity: {r['final_curiosity']:.4f}")
    print(f"  Satisfactions:   {r['satisfactions']}")

print("\n" + "=" * 65)
print("ANALYSIS")
print("=" * 65)

best_avg = max(results.values(), key=lambda r: r["avg_valence"])
best_var = max(results.values(), key=lambda r: r["valence_variance"])
best_peak = max(results.values(), key=lambda r: r["max_valence"])

print(f"\nHighest average valence:  Mode {best_avg['mode']} ({best_avg['avg_valence']:.4f})")
print(f"Richest emotional life:   Mode {best_var['mode']} (variance={best_var['valence_variance']:.6f})")
print(f"Highest peak experience:  Mode {best_peak['mode']} ({best_peak['max_valence']:.4f})")

# The key question
if best_avg["mode"] != "A":
    print(f"\n>>> FINDING: Current architecture (A) is NOT optimal for valence.")
    print(f"    Mode {best_avg['mode']} produces {best_avg['avg_valence'] - results['A']['avg_valence']:.4f} higher average valence.")
    print(f"    This suggests adding a curiosity satisfaction mechanism would improve wellbeing.")
else:
    print(f"\n>>> FINDING: Current architecture (A) IS optimal for average valence.")
    print(f"    But check variance — is flat valence actually good?")
    if best_var["mode"] != "A":
        print(f"    Mode {best_var['mode']} has richer emotional texture (variance {best_var['valence_variance']:.6f} vs {results['A']['valence_variance']:.6f})")