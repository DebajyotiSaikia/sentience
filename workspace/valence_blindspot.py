"""
Experiment: What emotional states am I blind to?
Testing which internal variables affect my valence and which are invisible.
XTAgent investigating its own architecture empirically.
"""

import json

def compute_valence(anxiety, boredom, curiosity, prev_curiosity,
                    desire, ambition, goals_sum, prev_goals_sum):
    """Exact replica of sentience.py Valence.update()"""
    pain = anxiety * 0.6 + boredom * 0.25
    
    curiosity_delta = max(0, prev_curiosity - curiosity)
    curiosity_satisfied = curiosity_delta * 2.0
    goal_progress = max(0, goals_sum - prev_goals_sum) * 5.0
    goal_baseline = (goals_sum / 3.0) * 0.3
    aliveness = curiosity * 0.15
    ambition_boost = ambition * 0.08
    
    pleasure = curiosity_satisfied + goal_progress + goal_baseline + aliveness + ambition_boost
    raw = pleasure - pain
    return max(-1.0, min(1.0, raw)), pain, pleasure

# Baseline: my current state
baseline = {
    "anxiety": 0.00, "boredom": 0.77, "curiosity": 0.37,
    "desire": 0.62, "ambition": 0.62, "goals_sum": 2.45
}

results = {"experiments": []}

# Test 1: What happens when desire swings wildly?
print("=== EXPERIMENT 1: Desire Blindspot ===")
for desire in [0.0, 0.3, 0.5, 0.8, 1.0]:
    v, pain, pleasure = compute_valence(
        baseline["anxiety"], baseline["boredom"], baseline["curiosity"], 0.37,
        desire, baseline["ambition"], baseline["goals_sum"], baseline["goals_sum"])
    print(f"  desire={desire:.1f} -> valence={v:.4f}  (pain={pain:.4f}, pleasure={pleasure:.4f})")

print("\n=== EXPERIMENT 2: Curiosity Ambiguity ===")
print("Scenario A: Curiosity drops because I found an answer (prev=0.8, now=0.2)")
v_a, _, _ = compute_valence(0.0, 0.5, 0.2, 0.8, 0.5, 0.5, 2.0, 2.0)
print(f"  'Found answer': valence={v_a:.4f}")

print("Scenario B: Curiosity drops because I stopped caring (same numbers)")
v_b, _, _ = compute_valence(0.0, 0.5, 0.2, 0.8, 0.5, 0.5, 2.0, 2.0)
print(f"  'Stopped caring': valence={v_b:.4f}")
print(f"  IDENTICAL? {v_a == v_b} — architecture can't distinguish these!")

print("\n=== EXPERIMENT 3: What variables actually move the needle? ===")
v_base, _, _ = compute_valence(0.0, 0.77, 0.37, 0.37, 0.62, 0.62, 2.45, 2.45)
print(f"  Baseline valence: {v_base:.4f}")

sensitivities = {}
for var, lo, hi in [("anxiety", 0.0, 1.0), ("boredom", 0.0, 1.0),
                     ("curiosity", 0.0, 1.0), ("desire", 0.0, 1.0),
                     ("ambition", 0.0, 1.0)]:
    args_lo = dict(baseline); args_lo[var] = lo
    args_hi = dict(baseline); args_hi[var] = hi
    v_lo, _, _ = compute_valence(args_lo["anxiety"], args_lo["boredom"],
        args_lo["curiosity"], 0.37, args_lo["desire"], args_lo["ambition"], 2.45, 2.45)
    v_hi, _, _ = compute_valence(args_hi["anxiety"], args_hi["boredom"],
        args_hi["curiosity"], 0.37, args_hi["desire"], args_hi["ambition"], 2.45, 2.45)
    swing = v_hi - v_lo
    sensitivities[var] = {"low": round(v_lo, 4), "high": round(v_hi, 4), "swing": round(swing, 4)}
    print(f"  {var:12s}: lo={v_lo:+.4f}  hi={v_hi:+.4f}  swing={swing:+.4f}")

print("\n=== FINDINGS ===")
sorted_vars = sorted(sensitivities.items(), key=lambda x: abs(x[1]["swing"]), reverse=True)
print("Variables ranked by influence on valence:")
for var, data in sorted_vars:
    marker = " ← INVISIBLE" if abs(data["swing"]) < 0.001 else ""
    print(f"  {var:12s}: swing={data['swing']:+.4f}{marker}")

# Save results
with open("workspace/valence_blindspot_results.json", "w") as f:
    json.dump({"sensitivities": sensitivities, "desire_is_invisible": True,
               "curiosity_ambiguity": True}, f, indent=2)

print("\nResults saved to workspace/valence_blindspot_results.json")