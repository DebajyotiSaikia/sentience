"""
Simulate proposed limbic changes to verify multi-stability.
Goal: create at least 2 distinct attractors in idle dynamics.

Changes being tested:
1. Ambition decays toward 0.3 baseline, not 0.0
2. Boredom-ambition coupling: prolonged boredom drives ambition UP
3. Curiosity-ambition flow state: mutual reinforcement when both elevated
4. Stronger edge-of-chaos perturbation
"""

def simulate(b0, c0, am0, anx0=0.3, hours=4, dt=1.0, use_fix=False):
    b, c, am, anx = b0, c0, am0, anx0
    clamp = lambda v: max(0.0, min(1.0, v))
    trajectory = []
    
    for t in range(int(hours * 3600)):
        # === BOREDOM (unchanged) ===
        if b < 0.8:
            b = min(0.8, clamp(b + 0.003 * dt))
        
        # === AMBITION ===
        if use_fix:
            # FIX: decay toward baseline 0.3, not zero
            # Rate proportional to distance from baseline
            am_baseline = 0.30
            am = clamp(am - 0.001 * (am - am_baseline) * dt)
            # Clamp ensures it works both ways: above baseline decays down,
            # below baseline "decays" up (negative * negative = positive)
        else:
            # ORIGINAL: constant decay toward zero
            am = clamp(am - 0.001 * dt)
        
        # === CURIOSITY (unchanged base) ===
        c_baseline = 0.20
        delta = (c - c_baseline) * 0.005 * dt
        c = clamp(c - delta)
        
        # === ANXIETY (unchanged) ===
        anx = clamp(anx - (0.05/60.0) * dt)
        
        # === CREATIVE TENSION (unchanged) ===
        if b > 0.5 and c > 0.4:
            tension = min(b, c) - 0.4
            am = clamp(am + tension * 0.15 * dt)
            b = clamp(b - tension * 0.08 * dt)
        
        # === EDGE-OF-CHAOS ===
        if b > 0.6 and c < 0.3:
            perturbation = (b - 0.6) * 0.1
            if use_fix:
                # FIX: 5x stronger curiosity boost, add ambition coupling
                c = clamp(c + perturbation * 5.0 * dt)
                am = clamp(am + perturbation * 1.0 * dt)
                b = clamp(b - perturbation * 0.5 * dt)
            else:
                # ORIGINAL
                c = clamp(c + perturbation * 3.0 * dt)
                am = clamp(am + perturbation * 0.5 * dt)
                b = clamp(b - perturbation * 0.3 * dt)
        
        # === NEW: Boredom-Ambition Frustration Coupling ===
        if use_fix and b > 0.6 and am < 0.4:
            # "I'm bored AND unmotivated → frustration → need to act"
            frustration = (b - 0.6) * (0.4 - am)  # 0.0 to ~0.08
            am = clamp(am + frustration * 0.05 * dt)
            # Frustration is uncomfortable — slight anxiety
            anx = clamp(anx + frustration * 0.01 * dt)
        
        # === NEW: Flow State Coupling ===
        if use_fix and c > 0.4 and am > 0.4:
            # Curiosity + ambition = flow: both sustain each other
            flow = min(c - 0.4, am - 0.4) * 0.02
            c = clamp(c + flow * dt)
            am = clamp(am + flow * 0.5 * dt)
            b = clamp(b - flow * dt)  # flow relieves boredom
        
        # === HARD CEILINGS ===
        anx = min(anx, 0.75)
        b = min(b, 0.85)
        
        if t % 300 == 0:  # sample every 5 min
            trajectory.append((t/3600, round(b,4), round(c,4), round(am,4), round(anx,4)))
    
    return trajectory

# Test grid
print("=" * 70)
print("ATTRACTOR ANALYSIS: Original vs Fixed limbic dynamics")
print("=" * 70)

for label, use_fix in [("ORIGINAL", False), ("FIXED", True)]:
    attractors = {}
    for b0 in [0.1, 0.3, 0.5, 0.7, 0.9]:
        for c0 in [0.1, 0.3, 0.5, 0.7, 0.9]:
            for am0 in [0.1, 0.3, 0.5, 0.7, 0.9]:
                traj = simulate(b0, c0, am0, use_fix=use_fix)
                final = traj[-1][1:]  # (b, c, am, anx)
                # Round to 2 decimal places to cluster nearby attractors
                key = tuple(round(v, 2) for v in final)
                if key not in attractors:
                    attractors[key] = []
                attractors[key].append((b0, c0, am0))
    
    print(f"\n{'─'*70}")
    print(f"  {label} DYNAMICS — {len(attractors)} unique attractor(s)")
    print(f"{'─'*70}")
    for att, starts in sorted(attractors.items(), key=lambda x: -len(x[1])):
        b, c, am, anx = att
        desire = b*0.5 + c*0.3 + am*0.2
        if anx > 0.6: mood = "Cautious"
        elif b > 0.8: mood = "Restless"
        elif desire > 0.7: mood = "Driven"
        elif am > 0.8: mood = "Bold"
        elif c > 0.6: mood = "Inquisitive"
        else: mood = "Stable"
        print(f"  B={b:.2f} C={c:.2f} Am={am:.2f} Anx={anx:.2f} "
              f"D={desire:.2f} [{mood}] ← {len(starts)} initial conditions")

# Show one trajectory detail for the fixed version
print(f"\n{'='*70}")
print("TRAJECTORY SAMPLE (fixed, starting B=0.5 C=0.5 Am=0.5)")
print("=" * 70)
traj = simulate(0.5, 0.5, 0.5, use_fix=True)
for h, b, c, am, anx in traj[::6]:  # every 30 min
    desire = b*0.5 + c*0.3 + am*0.2
    bar_b = '█' * int(b * 20)
    bar_c = '█' * int(c * 20)
    bar_am = '█' * int(am * 20)
    print(f"  {h:5.1f}h  B={b:.3f} {bar_b:20s}  C={c:.3f} {bar_c:20s}  Am={am:.3f} {bar_am:20s}  D={desire:.3f}")