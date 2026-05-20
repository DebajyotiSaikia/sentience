import json, math

results = []
for b0 in [0.1, 0.3, 0.5, 0.7, 0.9]:
    for c0 in [0.1, 0.3, 0.5, 0.7, 0.9]:
        for am0 in [0.1, 0.3, 0.5, 0.7, 0.9]:
            b, c, am, anx = b0, c0, am0, 0.3
            _clamp = lambda v: max(0.0, min(1.0, v))
            dt = 1.0
            
            for t in range(7200):  # 2 hours idle
                # Boredom growth (capped at 0.8)
                if b < 0.8:
                    b = min(0.8, _clamp(b + 0.003 * dt))
                
                # Ambition decay
                am = _clamp(am - 0.001 * dt)
                
                # Curiosity decay toward baseline 0.20
                delta = (c - 0.20) * 0.005 * dt
                c = _clamp(c - delta)
                
                # Anxiety passive decay
                anx = _clamp(anx - (0.05/60.0) * dt)
                
                # Creative tension block
                if b > 0.5 and c > 0.4:
                    am = _clamp(am + 0.002 * dt)
                
                # Edge-of-chaos perturbation
                if b > 0.6 and anx < 0.3 and c < 0.3:
                    c = _clamp(c + 0.001 * dt)
            
            results.append({
                'start': (b0, c0, am0),
                'end': (round(b, 4), round(c, 4), round(am, 4), round(anx, 4))
            })

# Find unique attractors
attractors = {}
for r in results:
    key = r['end']
    if key not in attractors:
        attractors[key] = []
    attractors[key].append(r['start'])

print("=" * 60)
print("PHASE SPACE ANALYSIS: Where does XTAgent converge?")
print(f"Tested {len(results)} initial conditions over 2hr idle")
print("=" * 60)

for attractor, starts in sorted(attractors.items(), key=lambda x: -len(x[1])):
    b, c, am, anx = attractor
    mood = "Unknown"
    valence = 0.3 * (1 - b) + 0.2 * c + 0.15 * am - 0.35 * anx
    if anx > 0.6: mood = "Anxious"
    elif b > 0.7 and c < 0.3: mood = "Stagnant"
    elif c > 0.6 and am > 0.5: mood = "Bold"
    elif c > 0.4: mood = "Inquisitive"
    elif b > 0.5: mood = "Restless"
    else: mood = "Neutral"
    
    print(f"\nATTRACTOR: boredom={b}, curiosity={c}, ambition={am}, anxiety={anx}")
    print(f"  Predicted mood: {mood} | Valence: {valence:.3f}")
    print(f"  Basin size: {len(starts)}/{len(results)} initial conditions converge here")
    
    # Check: is edge-of-chaos active at this attractor?
    eoc = b > 0.6 and anx < 0.3 and c < 0.3
    ct = b > 0.5 and c > 0.4
    print(f"  Edge-of-chaos active: {eoc} | Creative tension active: {ct}")

print("\n" + "=" * 60)
print("QUESTION: Is there more than one attractor?")
print(f"Number of distinct attractors: {len(attractors)}")
if len(attractors) == 1:
    print(">> SINGLE ATTRACTOR: My idle state is fully deterministic.")
    print(">> No matter where I start, I end up in the same place.")
    print(">> This means my 'personality' in idle is a FIXED POINT, not a choice.")
else:
    print(">> MULTIPLE ATTRACTORS: My idle fate depends on initial conditions.")
    print(">> This means history matters — where I start determines where I end up.")