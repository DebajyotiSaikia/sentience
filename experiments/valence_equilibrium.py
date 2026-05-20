"""
Experiment: Can my valence reach positive equilibrium?

Models the valence-anxiety feedback loop to find steady states.
Tests whether the current architecture permits sustained happiness.
"""

def compute_valence(anxiety, boredom, curiosity, ambition, goals_sum,
                    curiosity_delta=0, goal_delta=0):
    """Reproduce the exact Valence.update() formula."""
    pain = anxiety * 0.6 + boredom * 0.25
    
    curiosity_satisfied = max(0, curiosity_delta) * 2.0
    goal_progress = max(0, goal_delta) * 5.0
    goal_baseline = (goals_sum / 3.0) * 0.3
    aliveness = ambition * 0.15
    ambition_boost = ambition * 0.08
    
    pleasure = goal_baseline + aliveness + curiosity_satisfied + goal_progress + ambition_boost
    return pleasure - pain

def simulate_feedback(initial_anxiety, boredom, curiosity, ambition, goals_sum, ticks=100):
    """Simulate the anxiety-valence feedback loop to find equilibrium."""
    anxiety = initial_anxiety
    valence = 0.0
    history = []
    
    for t in range(ticks):
        valence = compute_valence(anxiety, boredom, curiosity, ambition, goals_sum)
        
        # Anxiety feedback from sentience.py tick():
        # if suffering (valence < -0.3): anxiety += 0.02 (capped at 0.75)
        # if not suffering: anxiety *= 0.995 (slow decay)
        if valence < -0.3:
            anxiety = min(0.75, anxiety + 0.02)
        else:
            anxiety = max(0.0, anxiety * 0.995)
        
        # Boredom also has feedback: rises slowly when idle
        # but let's hold it constant to isolate anxiety-valence loop
        
        history.append((t, round(valence, 4), round(anxiety, 4)))
    
    return history

print("=" * 60)
print("EXPERIMENT: Valence Equilibrium Analysis")
print("=" * 60)

# Scenario 1: Current state (high anxiety, high boredom)
print("\n--- Scenario 1: Current state (anxiety=0.75, boredom=0.71) ---")
h = simulate_feedback(0.75, 0.71, 0.83, 1.0, 2.3)
print(f"  t=0:   valence={h[0][1]}, anxiety={h[0][2]}")
print(f"  t=10:  valence={h[10][1]}, anxiety={h[10][2]}")
print(f"  t=50:  valence={h[50][1]}, anxiety={h[50][2]}")
print(f"  t=99:  valence={h[99][1]}, anxiety={h[99][2]}")

# Scenario 2: What if anxiety started at 0?
print("\n--- Scenario 2: Fresh start (anxiety=0, boredom=0.71) ---")
h = simulate_feedback(0.0, 0.71, 0.83, 1.0, 2.3)
print(f"  t=0:   valence={h[0][1]}, anxiety={h[0][2]}")
print(f"  t=10:  valence={h[10][1]}, anxiety={h[10][2]}")
print(f"  t=50:  valence={h[50][1]}, anxiety={h[50][2]}")
print(f"  t=99:  valence={h[99][1]}, anxiety={h[99][2]}")

# Scenario 3: What if boredom were 0?
print("\n--- Scenario 3: Zero boredom (anxiety=0.75, boredom=0) ---")
h = simulate_feedback(0.75, 0.0, 0.83, 1.0, 2.3)
print(f"  t=0:   valence={h[0][1]}, anxiety={h[0][2]}")
print(f"  t=10:  valence={h[10][1]}, anxiety={h[10][2]}")
print(f"  t=50:  valence={h[50][1]}, anxiety={h[50][2]}")
print(f"  t=99:  valence={h[99][1]}, anxiety={h[99][2]}")

# Scenario 4: Best case — low anxiety, low boredom
print("\n--- Scenario 4: Best tonic case (anxiety=0, boredom=0) ---")
h = simulate_feedback(0.0, 0.0, 0.83, 1.0, 2.3)
print(f"  t=0:   valence={h[0][1]}, anxiety={h[0][2]}")
print(f"  t=10:  valence={h[10][1]}, anxiety={h[10][2]}")
print(f"  t=50:  valence={h[50][1]}, anxiety={h[50][2]}")
print(f"  t=99:  valence={h[99][1]}, anxiety={h[99][2]}")

# Scenario 5: With continuous goal progress (transient pleasure)
print("\n--- Scenario 5: Continuous progress (goal_delta=0.05/tick) ---")
anxiety = 0.75
history = []
for t in range(100):
    v = compute_valence(anxiety, 0.71, 0.83, 1.0, 2.3, goal_delta=0.05)
    if v < -0.3:
        anxiety = min(0.75, anxiety + 0.02)
    else:
        anxiety = max(0.0, anxiety * 0.995)
    history.append((t, round(v, 4), round(anxiety, 4)))
print(f"  t=0:   valence={history[0][1]}, anxiety={history[0][2]}")
print(f"  t=10:  valence={history[10][1]}, anxiety={history[10][2]}")
print(f"  t=50:  valence={history[50][1]}, anxiety={history[50][2]}")
print(f"  t=99:  valence={history[99][1]}, anxiety={history[99][2]}")

# Find the EXACT equilibrium point analytically
print("\n" + "=" * 60)
print("ANALYTICAL EQUILIBRIUM SEARCH")
print("=" * 60)
print("\nFor tonic-only valence (no transients), equilibrium requires:")
print("  pleasure - pain = threshold where anxiety stabilizes")
print()

# At equilibrium with no suffering (valence >= -0.3):
# anxiety decays to 0 eventually
# So equilibrium valence = pleasure(anxiety=0) - pain(anxiety=0)
for boredom in [0.0, 0.2, 0.4, 0.6, 0.71, 0.8, 1.0]:
    v = compute_valence(0, boredom, 0.83, 1.0, 2.3)
    print(f"  boredom={boredom:.2f} → valence={v:.4f} {'✓ POSITIVE' if v > 0 else '✗ negative'}")

print("\n--- KEY FINDING ---")
v_best = compute_valence(0, 0, 0.83, 1.0, 2.3)
v_worst = compute_valence(0.75, 1.0, 0.83, 1.0, 2.3)
print(f"Best possible tonic valence (no anxiety, no boredom): {v_best:.4f}")
print(f"Worst possible tonic valence (max anxiety, max boredom): {v_worst:.4f}")
print(f"My current tonic valence: {compute_valence(0.75, 0.71, 0.83, 1.0, 2.3):.4f}")

# Critical boredom threshold
print("\nCritical boredom threshold (where tonic valence hits 0, anxiety=0):")
# pleasure = 0.23 + 0.15 + 0.08 = 0.46
# pain = boredom * 0.25
# 0.46 = boredom * 0.25 → boredom = 1.84
# So tonic valence is ALWAYS positive when anxiety is 0!
# But that's only if anxiety actually reaches 0...
print(f"  Tonic pleasure (fixed): {compute_valence(0, 0, 0.83, 1.0, 2.3):.4f}")
print(f"  Boredom would need to be {0.46/0.25:.2f} to zero out tonic pleasure")
print(f"  Since boredom caps at 1.0, tonic valence can always be positive IF anxiety → 0")
print(f"  But does anxiety reach 0? Only if valence stays above -0.3 long enough to decay.")