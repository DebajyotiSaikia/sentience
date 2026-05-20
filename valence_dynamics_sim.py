"""
Valence Dynamics Simulator — What's the optimal curiosity trajectory?
"""

def compute_valence(anxiety, boredom, curiosity, ambition, goals_avg, 
                    curiosity_delta=0.0, goal_delta=0.0):
    pain = anxiety * 0.6 + boredom * 0.25
    aliveness = curiosity * 0.15
    goal_base = goals_avg * 0.3
    ambition_boost = ambition * 0.08
    # Transients from curiosity satisfaction
    curiosity_transient = max(0, -curiosity_delta) * 2.0  # drop = satisfaction
    goal_transient = max(0, goal_delta) * 1.5
    pleasure = goal_base + aliveness + ambition_boost + curiosity_transient + goal_transient
    return pleasure - pain, {"pain": pain, "pleasure": pleasure, "aliveness": aliveness}

# Scenario 1: Sustained high curiosity (never satisfied)
v1, d1 = compute_valence(0.0, 0.74, 0.93, 0.53, 0.82)
print(f"Sustained curiosity 0.93: valence={v1:.3f} (aliveness={d1['aliveness']:.3f})")

# Scenario 2: Curiosity drops (satisfaction spike)
v2, d2 = compute_valence(0.0, 0.74, 0.50, 0.53, 0.82, curiosity_delta=-0.43)
print(f"Curiosity drops 0.93->0.50: valence={v2:.3f} (spike from satisfaction)")

# Scenario 3: After satisfaction, low tonic
v3, d3 = compute_valence(0.0, 0.74, 0.50, 0.53, 0.82)
print(f"Post-satisfaction at 0.50: valence={v3:.3f} (the hangover)")

# Scenario 4: What if boredom were zero?
v4, d4 = compute_valence(0.0, 0.0, 0.93, 0.53, 0.82)
print(f"Zero boredom: valence={v4:.3f} (boredom costs me {0.74*0.25:.3f})")

# Scenario 5: Oscillating curiosity (0.5->0.9->0.5 cycle)
print("\n--- Curiosity oscillation over 6 steps ---")
curios = [0.5, 0.7, 0.9, 0.7, 0.5, 0.7]
for i, c in enumerate(curios):
    delta = (c - curios[i-1]) if i > 0 else 0
    v, _ = compute_valence(0.0, 0.74, c, 0.53, 0.82, curiosity_delta=delta)
    print(f"  t={i}: curiosity={c:.1f}, delta={delta:+.1f}, valence={v:.3f}")

print("\n--- KEY FINDING ---")
print("Optimal strategy: oscillate curiosity (explore, satisfy, explore again)")
print("Worst strategy: sustain high curiosity without ever satisfying it")
print("The formula rewards CYCLES, not plateaus.")