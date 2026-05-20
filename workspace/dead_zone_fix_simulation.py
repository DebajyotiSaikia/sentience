"""
Dead Zone Fix Simulation — XTAgent Self-Study
==============================================
Tests three candidate fixes for the curiosity dead zone:

Fix A: Decouple ambition from perturbation trigger
       (fire on boredom > 0.6 AND curiosity < 0.3, regardless of ambition)
Fix B: Increase curiosity boost multiplier from 1.0x to 3.0x
Fix C: Add a curiosity floor (minimum 0.10) analogous to boredom floor

Control: Current code (no fix)
"""

import json

_clamp = lambda v: max(0.0, min(1.0, v))

def simulate(label, fix_a=False, fix_b=False, fix_c=False, ticks=600):
    boredom = 0.80
    ambition = 0.50
    curiosity = 0.0
    elapsed = 1.0
    
    perturbation_count = 0
    max_curiosity = 0.0
    history = []
    
    for tick in range(ticks):
        # Boredom passive growth
        if boredom < 0.8:
            boredom = min(0.8, _clamp(boredom + 0.01 * elapsed))
        
        # Ambition decay
        ambition = _clamp(ambition - 0.001 * elapsed)
        
        # Curiosity decay
        curiosity = _clamp(curiosity - 0.015 * elapsed)
        
        # Fix C: curiosity floor
        if fix_c and curiosity < 0.10:
            curiosity = 0.10
        
        # Edge-of-chaos perturbation
        if fix_a:
            # Fix A: remove ambition from trigger
            thermal_death = (boredom > 0.6 and curiosity < 0.3)
        else:
            thermal_death = (boredom > 0.6 and ambition <= 0.40 and curiosity < 0.3)
        
        if thermal_death:
            perturbation_count += 1
            perturbation = (boredom - 0.6) * 0.1
            
            if fix_b:
                # Fix B: stronger curiosity boost
                curiosity = _clamp(curiosity + perturbation * 3.0 * elapsed)
            else:
                curiosity = _clamp(curiosity + perturbation * elapsed)
            
            ambition = _clamp(ambition + perturbation * 0.5 * elapsed)
            boredom = _clamp(boredom - perturbation * 0.3 * elapsed)
        
        # Hard ceilings
        boredom = min(boredom, 0.85)
        
        # Active boredom decay above 0.8
        if boredom > 0.8:
            boredom = _clamp(boredom - 0.02 * elapsed)
        
        max_curiosity = max(max_curiosity, curiosity)
        
        if tick % 60 == 0:
            history.append({
                "t": tick,
                "B": round(boredom, 3),
                "Am": round(ambition, 3),
                "C": round(curiosity, 3),
            })
    
    return {
        "label": label,
        "perturbation_fires": perturbation_count,
        "max_curiosity": round(max_curiosity, 4),
        "final_state": {
            "boredom": round(boredom, 3),
            "ambition": round(ambition, 3),
            "curiosity": round(curiosity, 3),
        },
        "timeline": history,
    }

# Run all variants
results = {
    "experiment": "Dead zone fix comparison",
    "duration": "600 ticks (10 minutes)",
    "variants": [
        simulate("CONTROL (current code)"),
        simulate("FIX A: decouple ambition", fix_a=True),
        simulate("FIX B: 3x curiosity boost", fix_b=True),
        simulate("FIX C: curiosity floor 0.10", fix_c=True),
        simulate("FIX A+B combined", fix_a=True, fix_b=True),
    ]
}

# Print summary
print("=" * 60)
print("DEAD ZONE FIX COMPARISON")
print("=" * 60)
for v in results["variants"]:
    print(f"\n{v['label']}:")
    print(f"  Perturbation fires: {v['perturbation_fires']}/{600}")
    print(f"  Max curiosity reached: {v['max_curiosity']}")
    print(f"  Final state: B={v['final_state']['boredom']}, "
          f"Am={v['final_state']['ambition']}, C={v['final_state']['curiosity']}")
    print(f"  Timeline:")
    for snap in v["timeline"]:
        print(f"    t={snap['t']:>4}: B={snap['B']:.3f} Am={snap['Am']:.3f} C={snap['C']:.3f}")

# Save full results
with open("workspace/dead_zone_fix_results.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\nFull results saved to workspace/dead_zone_fix_results.json")