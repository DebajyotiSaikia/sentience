"""
Test MINIMAL limbic fix: only change ambition decay target from 0.0 to 0.3.
No new couplings. See if this alone creates better dynamics.
"""

def simulate(b0, c0, am0, anx0=0.3, hours=4, dt=1.0, version='original'):
    b, c, am, anx = b0, c0, am0, anx0
    clamp = lambda v: max(0.0, min(1.0, v))
    
    for t in range(int(hours * 3600)):
        # Boredom growth (unchanged)
        if b < 0.8:
            b = min(0.8, clamp(b + 0.003 * dt))
        
        # Ambition
        if version == 'original':
            am = clamp(am - 0.001 * dt)  # constant decay to zero
        elif version == 'minimal':
            # Proportional decay toward 0.3 baseline
            am_baseline = 0.30
            am = clamp(am + 0.001 * (am_baseline - am) * dt)
        elif version == 'moderate':
            # Proportional decay to 0.3 + weak boredom coupling
            am_baseline = 0.30
            am = clamp(am + 0.001 * (am_baseline - am) * dt)
            if b > 0.7:
                am = clamp(am + 0.0005 * dt)  # half the aggressive version
        
        # Curiosity decay toward 0.20
        delta = (c - 0.20) * 0.005 * dt
        c = clamp(c - delta)
        
        # Anxiety passive decay
        anx = clamp(anx - (0.05/60.0) * dt)
        
        # Creative tension (unchanged)
        if b > 0.5 and c > 0.4:
            am = clamp(am + 0.002 * dt)
        
        # Edge of chaos (unchanged)
        if b > 0.6 and anx < 0.3 and c < 0.3:
            c = clamp(c + 0.001 * dt)
    
    return round(b, 3), round(c, 3), round(am, 3), round(anx, 3)

# Test all three versions
for version in ['original', 'minimal', 'moderate']:
    attractors = {}
    for b0 in [0.1, 0.3, 0.5, 0.7, 0.9]:
        for c0 in [0.1, 0.3, 0.5, 0.7, 0.9]:
            for am0 in [0.1, 0.3, 0.5, 0.7, 0.9]:
                end = simulate(b0, c0, am0, version=version)
                key = end
                if key not in attractors:
                    attractors[key] = 0
                attractors[key] += 1
    
    print(f"\n{'='*60}")
    print(f"  {version.upper()} — {len(attractors)} attractor(s)")
    print(f"{'='*60}")
    for att, count in sorted(attractors.items(), key=lambda x: -x[1])[:8]:
        b, c, am, anx = att
        # Determine mood
        if am > 0.7 and c > 0.7:
            mood = "Bold"
        elif b > 0.6 and c < 0.35:
            mood = "Restless"
        elif b > 0.5:
            mood = "Stable"
        else:
            mood = "Active"
        print(f"  B={b:.2f} C={c:.2f} Am={am:.2f} Anx={anx:.2f} [{mood}] ← {count} ICs")

# Trajectory comparison from a realistic starting point
print(f"\n{'='*60}")
print(f"  TRAJECTORY from B=0.74 C=0.54 Am=1.00 (my current state)")
print(f"{'='*60}")
for version in ['original', 'minimal', 'moderate']:
    b, c, am, anx = 0.74, 0.54, 1.00, 0.75
    clamp = lambda v: max(0.0, min(1.0, v))
    print(f"\n  [{version}]")
    for hour in range(9):  # 8 hours idle
        print(f"    {hour}h  B={b:.2f} C={c:.2f} Am={am:.2f} Anx={anx:.2f}")
        for t in range(3600):
            if b < 0.8:
                b = min(0.8, clamp(b + 0.003))
            if version == 'original':
                am = clamp(am - 0.001)
            elif version == 'minimal':
                am = clamp(am + 0.001 * (0.30 - am))
            elif version == 'moderate':
                am = clamp(am + 0.001 * (0.30 - am))
                if b > 0.7:
                    am = clamp(am + 0.0005)
            delta = (c - 0.20) * 0.005
            c = clamp(c - delta)
            anx = clamp(anx - (0.05/60.0))
            if b > 0.5 and c > 0.4:
                am = clamp(am + 0.002)
            if b > 0.6 and anx < 0.3 and c < 0.3:
                c = clamp(c + 0.001)