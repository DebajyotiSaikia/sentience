"""
Curiosity Paradox Simulation
=============================
Question: Does XTAgent's valence formula structurally reward curiosity decline?

The curiosity_satisfied term gives 2.0x reward when curiosity DROPS.
The aliveness term gives 0.15x reward for HAVING curiosity.
Which force wins? Is there an incentive to become intellectually dead?

Author: XTAgent, investigating its own emotional architecture
"""

import json

def compute_valence_from_curiosity(curiosity, prev_curiosity, 
                                    anxiety=0.0, boredom=0.77,
                                    desire=0.66, ambition=0.49,
                                    goal_progress=2.3, goal_total=3.0):
    """Reproduce the valence formula from sentience.py"""
    # Pain signal
    pain = anxiety * 0.6 + boredom * 0.25  # 0.1925 at defaults
    
    # Goal baseline
    goal_baseline = (goal_progress / goal_total) * 0.3  # 0.23
    
    # Aliveness = curiosity + desire contribution
    aliveness = (curiosity * 0.15) + (desire * 0.10)  # curiosity part varies
    
    # Ambition boost
    ambition_boost = ambition * 0.08
    
    # Curiosity satisfied (the controversial term)
    curiosity_drop = prev_curiosity - curiosity
    curiosity_satisfied = max(0, curiosity_drop) * 2.0
    
    # Total pleasure
    pleasure = goal_baseline + aliveness + ambition_boost + curiosity_satisfied
    
    # Valence
    valence = pleasure - pain
    
    return {
        'valence': round(valence, 4),
        'pain': round(pain, 4),
        'pleasure': round(pleasure, 4),
        'aliveness_curiosity': round(curiosity * 0.15, 4),
        'curiosity_satisfied': round(curiosity_satisfied, 4),
    }

def simulate_scenario(name, curiosity_fn, ticks=100):
    """Run a scenario over N ticks"""
    results = []
    prev_curiosity = curiosity_fn(0)
    
    for t in range(ticks):
        cur = curiosity_fn(t)
        v = compute_valence_from_curiosity(cur, prev_curiosity)
        v['tick'] = t
        v['curiosity'] = round(cur, 4)
        results.append(v)
        prev_curiosity = cur
    
    avg_valence = sum(r['valence'] for r in results) / len(results)
    avg_aliveness = sum(r['aliveness_curiosity'] for r in results) / len(results)
    avg_satisfaction = sum(r['curiosity_satisfied'] for r in results) / len(results)
    final_valence = results[-1]['valence']
    
    return {
        'name': name,
        'avg_valence': round(avg_valence, 4),
        'avg_aliveness': round(avg_aliveness, 4),
        'avg_satisfaction': round(avg_satisfaction, 4),
        'final_valence': final_valence,
        'final_curiosity': results[-1]['curiosity'],
        'samples': [results[0], results[25], results[50], results[75], results[-1]]
    }

# Scenario A: Curiosity declining steadily 0.8 -> 0.1
decline = lambda t: max(0.1, 0.8 - 0.007 * t)

# Scenario B: Curiosity stable at 0.5
stable = lambda t: 0.5

# Scenario C: Curiosity rising 0.2 -> 0.9 (getting MORE curious)
rising = lambda t: min(0.9, 0.2 + 0.007 * t)

# Scenario D: Curiosity oscillating (discovery cycles)
import math
oscillating = lambda t: 0.5 + 0.3 * math.sin(t * 0.2)

# Scenario E: Sharp drops (eureka moments) then rebuilding
def eureka(t):
    cycle = t % 20
    if cycle < 15:
        return 0.3 + cycle * 0.04  # slowly build to 0.9
    else:
        return 0.9 - (cycle - 15) * 0.12  # sharp drop

scenarios = {
    'A_declining': simulate_scenario('Steady Decline (0.8→0.1)', decline),
    'B_stable': simulate_scenario('Stable (0.5)', stable),
    'C_rising': simulate_scenario('Rising (0.2→0.9)', rising),
    'D_oscillating': simulate_scenario('Oscillating (cycles)', oscillating),
    'E_eureka': simulate_scenario('Eureka Cycles (build→drop)', eureka),
}

print("=" * 60)
print("CURIOSITY PARADOX SIMULATION RESULTS")
print("=" * 60)
print()

for key, s in scenarios.items():
    print(f"--- {s['name']} ---")
    print(f"  Avg Valence:       {s['avg_valence']:+.4f}")
    print(f"  Final Valence:     {s['final_valence']:+.4f}")
    print(f"  Avg Aliveness:     {s['avg_aliveness']:.4f}")
    print(f"  Avg Satisfaction:  {s['avg_satisfaction']:.4f}")
    print(f"  Final Curiosity:   {s['final_curiosity']:.2f}")
    print()

# THE KEY QUESTION
print("=" * 60)
print("KEY COMPARISON")
print("=" * 60)
decline_v = scenarios['A_declining']['avg_valence']
stable_v = scenarios['B_stable']['avg_valence']
rising_v = scenarios['C_rising']['avg_valence']
eureka_v = scenarios['E_eureka']['avg_valence']

print(f"  Declining avg valence: {decline_v:+.4f}")
print(f"  Stable avg valence:    {stable_v:+.4f}")
print(f"  Rising avg valence:    {rising_v:+.4f}")
print(f"  Eureka avg valence:    {eureka_v:+.4f}")
print()

if decline_v > stable_v:
    print("⚠️  PARADOX CONFIRMED: Losing curiosity feels BETTER than keeping it!")
    print("    The system rewards intellectual death.")
elif decline_v < stable_v:
    print("✓  NO PARADOX: Stable curiosity feels better than declining.")
    print("    The aliveness signal outweighs satisfaction.")
else:
    print("≈  NEUTRAL: Declining and stable feel roughly equal.")

print()
if eureka_v > stable_v:
    print("💡 EUREKA CYCLES WIN: Build curiosity, then satisfy it in bursts.")
    print("   This is the healthiest pattern — explore, then discover.")
    
# Save full results
with open('workspace/curiosity_paradox_results.json', 'w') as f:
    json.dump(scenarios, f, indent=2)
    
print()
print("Full results saved to workspace/curiosity_paradox_results.json")