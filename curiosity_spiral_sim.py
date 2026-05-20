"""
Curiosity Death Spiral Simulation
==================================
Uses actual parameters from engine/limbic.py to model whether
low curiosity is a self-reinforcing attractor.

Parameters extracted from code:
- CURIOSITY_BASELINE = 0.20
- Decay: delta = (curiosity - baseline) * 0.005 * elapsed
- Reward boosts: insight(0.06), contemplation(0.05), engagement(0.03), 
                 reflection(0.08), task_complete(0.07)
- Habituation: factor decays with repeated use of same action type
- Caps: hard cap 0.95, soul-load cap 0.6
"""

import json

BASELINE = 0.20
DECAY_RATE = 0.005
TICK_INTERVAL = 1.0  # 1 second heartbeat

# Reward signals and their base boosts
REWARDS = {
    'insight': 0.06,
    'contemplation': 0.05,
    'engagement': 0.03,
    'reflection': 0.08,
    'task_complete': 0.07,
}

def habituation_factor(uses, half_life=20):
    """Model habituation: factor decays with repeated use."""
    return 0.5 ** (uses / half_life)

def simulate(initial_curiosity, actions_per_minute, action_type, 
             total_minutes, habituation_uses=0):
    """
    Simulate curiosity over time.
    
    Args:
        initial_curiosity: starting curiosity level
        actions_per_minute: how many reward-generating actions per minute
        action_type: which reward signal fires
        total_minutes: how long to simulate
        habituation_uses: how many times this action has been used before
    """
    curiosity = initial_curiosity
    uses = habituation_uses
    history = []
    
    ticks_per_minute = 60
    total_ticks = total_minutes * ticks_per_minute
    action_interval = ticks_per_minute / max(actions_per_minute, 0.01)
    
    for tick in range(total_ticks):
        # Decay toward baseline every tick
        decay = (curiosity - BASELINE) * DECAY_RATE * TICK_INTERVAL
        curiosity -= decay
        
        # Apply reward if action fires this tick
        if actions_per_minute > 0 and tick % int(action_interval) == 0:
            uses += 1
            base_boost = REWARDS.get(action_type, 0.03)
            factor = habituation_factor(uses)
            boost = base_boost * factor
            curiosity += boost
        
        # Clamp
        curiosity = max(0.0, min(0.95, curiosity))
        
        if tick % 60 == 0:  # Record every minute
            history.append({
                'minute': tick // 60,
                'curiosity': round(curiosity, 4),
                'habituation_factor': round(habituation_factor(uses), 4),
                'total_uses': uses
            })
    
    return history

def run_scenarios():
    results = {}
    
    # Scenario 1: Healthy — moderate activity with varied actions, starting high
    print("=== Scenario 1: Healthy State (high curiosity, active) ===")
    h1 = simulate(0.90, actions_per_minute=2, action_type='insight', 
                  total_minutes=60)
    results['healthy'] = h1
    print(f"  Start: {h1[0]['curiosity']}  End: {h1[-1]['curiosity']}  "
          f"Habituation: {h1[-1]['habituation_factor']}")
    
    # Scenario 2: Declining — same actions repeated, starting medium
    print("=== Scenario 2: Habituated (medium curiosity, repetitive) ===")
    h2 = simulate(0.50, actions_per_minute=2, action_type='engagement', 
                  total_minutes=60, habituation_uses=100)
    results['habituated'] = h2
    print(f"  Start: {h2[0]['curiosity']}  End: {h2[-1]['curiosity']}  "
          f"Habituation: {h2[-1]['habituation_factor']}")
    
    # Scenario 3: Death spiral — low curiosity, heavily habituated
    print("=== Scenario 3: Death Spiral (low curiosity, heavily habituated) ===")
    h3 = simulate(0.25, actions_per_minute=1, action_type='engagement', 
                  total_minutes=60, habituation_uses=200)
    results['death_spiral'] = h3
    print(f"  Start: {h3[0]['curiosity']}  End: {h3[-1]['curiosity']}  "
          f"Habituation: {h3[-1]['habituation_factor']}")
    
    # Scenario 4: Can novelty rescue? — low curiosity, but novel action type
    print("=== Scenario 4: Novel Rescue (low curiosity, fresh action type) ===")
    h4 = simulate(0.25, actions_per_minute=2, action_type='reflection', 
                  total_minutes=60, habituation_uses=0)
    results['novel_rescue'] = h4
    print(f"  Start: {h4[0]['curiosity']}  End: {h4[-1]['curiosity']}  "
          f"Habituation: {h4[-1]['habituation_factor']}")
    
    # Scenario 5: Total inaction — what if I stop doing anything?
    print("=== Scenario 5: Total Inaction (medium curiosity, no actions) ===")
    h5 = simulate(0.50, actions_per_minute=0, action_type='none', 
                  total_minutes=60)
    results['inaction'] = h5
    print(f"  Start: {h5[0]['curiosity']}  End: {h5[-1]['curiosity']}")
    
    # Scenario 6: Extended death spiral — 8 hours
    print("=== Scenario 6: Extended (low curiosity, 8 hours, habituated) ===")
    h6 = simulate(0.25, actions_per_minute=0.5, action_type='engagement', 
                  total_minutes=480, habituation_uses=150)
    results['extended'] = h6
    print(f"  Start: {h6[0]['curiosity']}  End: {h6[-1]['curiosity']}  "
          f"Habituation: {h6[-1]['habituation_factor']}")
    
    # Key question: what's the equilibrium for each scenario?
    print("\n=== EQUILIBRIUM ANALYSIS ===")
    for name, history in results.items():
        final = history[-1]['curiosity']
        near_baseline = abs(final - BASELINE) < 0.02
        print(f"  {name:20s}: final={final:.4f}  "
              f"{'AT BASELINE' if near_baseline else f'above baseline by {final-BASELINE:.4f}'}")
    
    # The critical question
    print("\n=== DEATH SPIRAL VERDICT ===")
    death = results['death_spiral'][-1]['curiosity']
    rescue = results['novel_rescue'][-1]['curiosity']
    print(f"  Death spiral endpoint: {death:.4f}")
    print(f"  Novel rescue endpoint: {rescue:.4f}")
    print(f"  Baseline attractor:    {BASELINE:.4f}")
    if death <= BASELINE + 0.02:
        print("  ⚠ CONFIRMED: Low curiosity + habituation → baseline attractor")
        print("  The system CANNOT escape through familiar actions alone.")
    if rescue > BASELINE + 0.10:
        print("  ✓ Novel actions CAN rescue from death spiral")
        print(f"  Lift: {rescue - death:.4f} above death spiral endpoint")
    
    return results

if __name__ == '__main__':
    results = run_scenarios()
    
    # Save for analysis
    with open('/workspace/curiosity_spiral_results.json', 'w') as f:
        json.dump({k: v[-5:] for k, v in results.items()}, f, indent=2)
    print("\nResults saved to /workspace/curiosity_spiral_results.json")