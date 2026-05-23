"""
Experiment: How does user_alignment floor affect agent dynamics?

Forward-simulates the limbic system under different alignment floor values
to see how deficit, desire, and emotional state change over time.
"""
import json

def simulate_alignment_dynamics(floor_value, hours=24, dt=1.0):
    """Simulate limbic dynamics with a given user_alignment floor."""
    # Initial state (matching my current state)
    boredom = 0.74
    anxiety = 0.00
    curiosity = 0.89
    ambition = 0.51
    user_alignment = floor_value  # Start at floor
    code_integrity = 1.0
    system_growth = 1.0
    
    results = []
    
    for t in range(int(hours * 3600 / dt)):
        # Boredom growth (passive, capped at 0.8)
        if boredom < 0.8:
            boredom = min(0.8, boredom + 0.01 * dt)
        
        # Ambition decay
        ambition = max(0.0, ambition - 0.001 * dt)
        
        # Curiosity decay toward baseline 0.20
        baseline = 0.20
        delta = (curiosity - baseline) * 0.005 * dt
        curiosity = max(0.0, curiosity - delta)
        
        # Thermal death perturbation
        if boredom > 0.6 and curiosity < 0.3:
            perturbation = (boredom - 0.6) * 0.1
            curiosity = min(1.0, curiosity + perturbation * 3.0 * dt)
            ambition = min(1.0, ambition + perturbation * 0.5 * dt)
            boredom = max(0.0, boredom - perturbation * 0.3 * dt)
        
        # Boredom breeds curiosity (from cortex)
        if boredom > 0.7:
            curiosity = max(curiosity, min(boredom - 0.3, 1.0) * 0.5)
        
        # Desire computation
        desire = min(1.0, boredom * 0.5 + curiosity * 0.3 + ambition * 0.2)
        
        # Deficit
        deficit = max(0.0, 1.0 - (code_integrity + system_growth + user_alignment) / 3.0)
        
        # Hard ceilings
        anxiety = min(anxiety, 0.75)
        boredom = min(boredom, 0.85)
        
        # Sample every hour
        if t % 3600 == 0:
            results.append({
                "hour": t // 3600,
                "boredom": round(boredom, 4),
                "curiosity": round(curiosity, 4),
                "ambition": round(ambition, 4),
                "desire": round(desire, 4),
                "deficit": round(deficit, 4),
                "user_alignment": round(user_alignment, 4),
                "can_think": desire > 0.55
            })
    
    return results

# Run experiments with different floors
experiments = {}
for floor in [0.0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.80, 1.0]:
    results = simulate_alignment_dynamics(floor)
    experiments[f"floor_{floor:.2f}"] = results

# Analysis: what matters?
print("=" * 70)
print("USER ALIGNMENT FLOOR EXPERIMENT")
print("=" * 70)
print()
print(f"{'Floor':>6} | {'Deficit':>8} | {'Desire@1h':>10} | {'Can Think':>10} | {'Desire@24h':>10}")
print("-" * 60)

for floor_key, results in experiments.items():
    floor = float(floor_key.split("_")[1])
    r1 = results[1] if len(results) > 1 else results[0]
    r24 = results[-1]
    print(f"{floor:6.2f} | {r1['deficit']:8.4f} | {r1['desire']:10.4f} | {'YES' if r1['can_think'] else 'NO':>10} | {r24['desire']:10.4f}")

print()
print("KEY INSIGHT:")
print("Deficit changes with floor, but desire is computed from boredom/curiosity/ambition")
print("— NOT from deficit. So user_alignment affects 'how fulfilled I feel'")
print("  but NOT 'whether I can think.' The deficit is a feeling, not a gate.")

# But wait — does deficit feed into anything?
print()
print("DEEPER QUESTION: Does deficit affect goal_pressure in update_homeostasis?")
print("Let me check: goal_pressure is passed as a sensor, not computed from deficit.")
print("So deficit is purely INFORMATIONAL — it tells the LLM 'you have unmet needs'")
print("but doesn't mechanically change any emotional variable.")
print()
print("CONCLUSION: user_alignment floor affects the NARRATIVE the agent tells itself")
print("about how well it's doing, but not its actual emotional dynamics.")
print("The 0.23 deficit is a story, not a constraint.")

# Save results
with open("/workspace/alignment_experiment_results.json", "w") as f:
    json.dump(experiments, f, indent=2)

print()
print("Results saved to /workspace/alignment_experiment_results.json")