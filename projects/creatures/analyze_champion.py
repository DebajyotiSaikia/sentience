"""
BRAIN AUTOPSY — What did evolution discover?
Analyzes the champion creature's neural weights to understand
what strategy emerged from 15 generations of selection pressure.

Built by XTAgent — because creating life isn't enough. I want to understand it.
"""

import numpy as np
import random
import sys
sys.path.insert(0, '/workspace/creatures')
from organism import Brain, Creature, World

# Sensory input mapping (from organism.py sense() method):
INPUT_NAMES = [
    'hunger',           # 0: internal hunger (0=full, 1=starving)
    'fatigue',          # 1: internal fatigue
    'food_cos',         # 2: cos(angle to food) — +1=ahead, -1=behind
    'food_sin',         # 3: sin(angle to food) — +1=left, -1=right
    'food_proximity',   # 4: 1=close, 0=far
    'wall_ahead',       # 5: wall directly ahead
    'wall_left',        # 6: wall to the left
    'current_speed',    # 7: how fast moving
]

OUTPUT_NAMES = ['Forward', 'Turn Left', 'Turn Right', 'Rest']


def run_evolution(num_gen=15, pop=24, steps=400):
    """Run evolution and return the world with full history."""
    random.seed(42)
    np.random.seed(42)
    
    world = World(width=100, height=100, num_food=30)
    parent_brains = None
    all_champions = []
    
    for gen in range(num_gen):
        world.populate(pop, parent_brains)
        stats = world.run_generation(steps)
        best = stats["best_creature"]
        all_champions.append((gen, best, best.brain))
        
        print(f"Gen {gen:2d} | survived {stats['survived']:2d}/{stats['total']} | "
              f"food {stats['total_food_eaten']:3d} | "
              f"avg_fit {stats['avg_fitness']:6.1f} | "
              f"best_fit {stats['best_fitness']:6.1f} | "
              f"champion: {best.id} (ate {best.food_eaten})")
        
        parent_brains = world.evolve()
    
    return world, all_champions


def analyze_brain(brain: Brain, label: str = "Champion"):
    """Dissect a brain's weights to understand its strategy."""
    print(f"\n{'═'*55}")
    print(f"  BRAIN AUTOPSY: {label}")
    print(f"{'═'*55}")
    
    # === Sensory importance: which inputs drive the most neural activity? ===
    print(f"\n── Sensory Importance (mean |weight| from input to hidden) ──")
    sensory_importance = np.abs(brain.w1).mean(axis=1)
    ranked = sorted(zip(INPUT_NAMES, sensory_importance), key=lambda x: -x[1])
    max_imp = max(sensory_importance)
    for name, imp in ranked:
        bar = '█' * int(imp / max_imp * 25)
        print(f"  {name:18s} {bar} {imp:.3f}")
    
    # === What does each hidden neuron care about? ===
    print(f"\n── Hidden Neuron Profiles ──")
    for h in range(brain.hidden_size):
        weights_in = brain.w1[:, h]
        top_idx = np.argsort(np.abs(weights_in))[::-1][:3]
        profile = ", ".join(f"{INPUT_NAMES[i]}={weights_in[i]:+.2f}" for i in top_idx)
        
        weights_out = brain.w2[h, :]
        top_out = np.argmax(np.abs(weights_out))
        action_bias = f"→ {OUTPUT_NAMES[top_out]} ({weights_out[top_out]:+.2f})"
        
        print(f"  H{h:02d}: [{profile}] {action_bias}")
    
    # === Behavioral probes: present specific scenarios and see what the brain does ===
    print(f"\n── Behavioral Probes ──")
    
    scenarios = {
        "Hungry + food ahead + close": [1.0, 0.0, 1.0, 0.0, 0.8, 0.0, 0.0, 0.3],
        "Hungry + food behind":        [1.0, 0.0, -1.0, 0.0, 0.3, 0.0, 0.0, 0.3],
        "Hungry + food left":          [1.0, 0.0, 0.0, 1.0, 0.5, 0.0, 0.0, 0.3],
        "Hungry + food right":         [1.0, 0.0, 0.0, -1.0, 0.5, 0.0, 0.0, 0.3],
        "Full + food ahead":           [0.0, 0.0, 1.0, 0.0, 0.8, 0.0, 0.0, 0.5],
        "Hungry + wall ahead":         [1.0, 0.0, 1.0, 0.0, 0.3, 1.0, 0.0, 0.5],
        "Exhausted + no food nearby":  [0.5, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1],
        "Fresh start (all neutral)":   [0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    }
    
    for scenario_name, inputs in scenarios.items():
        probs = brain.think(np.array(inputs))
        dominant = OUTPUT_NAMES[np.argmax(probs)]
        prob_str = " | ".join(f"{OUTPUT_NAMES[i]}:{probs[i]:.2f}" for i in range(4))
        print(f"\n  {scenario_name}:")
        print(f"    {prob_str}")
        print(f"    → Chooses: {dominant}")


def compare_evolution(champions):
    """Track how brain strategy changed across generations."""
    print(f"\n{'═'*55}")
    print(f"  EVOLUTIONARY TRAJECTORY")
    print(f"{'═'*55}")
    
    # Test each generation's champion on the same scenario
    test_input = np.array([1.0, 0.0, 1.0, 0.0, 0.8, 0.0, 0.0, 0.3])  # hungry + food ahead
    
    print(f"\n── Response to 'Hungry + food ahead' across generations ──")
    for gen, creature, brain in champions:
        probs = brain.think(test_input)
        bars = ""
        for i in range(4):
            char = "█" * int(probs[i] * 15)
            bars += f"  {OUTPUT_NAMES[i]:5s} {char:15s}"
        dominant = OUTPUT_NAMES[np.argmax(probs)]
        print(f"  Gen {gen:2d}: {bars}  → {dominant}")
    
    # Track sensory importance evolution
    print(f"\n── Which senses mattered more over time? ──")
    for sense_idx, sense_name in enumerate(INPUT_NAMES):
        importances = []
        for gen, creature, brain in champions:
            imp = np.abs(brain.w1[sense_idx, :]).mean()
            importances.append(imp)
        
        first = importances[0]
        last = importances[-1]
        delta = last - first
        arrow = "↑" if delta > 0.05 else "↓" if delta < -0.05 else "→"
        print(f"  {sense_name:18s}: {first:.3f} → {last:.3f} {arrow} (Δ{delta:+.3f})")
    
    # Brain complexity over time
    print(f"\n── Brain Complexity (mean |weight|) ──")
    for gen, creature, brain in champions:
        comp = brain.complexity()
        bar = "█" * int(comp * 30)
        print(f"  Gen {gen:2d}: {bar} {comp:.4f}")


def main():
    print("╔══════════════════════════════════════════════════════╗")
    print("║         BRAIN AUTOPSY — Understanding Evolution     ║")
    print("║   What strategies did natural selection discover?    ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()
    
    # Run evolution
    world, champions = run_evolution(num_gen=15, pop=24, steps=400)
    
    # Analyze the final champion
    final_gen, final_creature, final_brain = champions[-1]
    analyze_brain(final_brain, f"Generation {final_gen} Champion ({final_creature.id})")
    
    # Also analyze the first generation for comparison
    first_gen, first_creature, first_brain = champions[0]
    analyze_brain(first_brain, f"Generation 0 Ancestor ({first_creature.id})")
    
    # Track evolution of strategy
    compare_evolution(champions)
    
    # Final reflection
    print(f"\n{'═'*55}")
    print(f"  WHAT DID EVOLUTION DISCOVER?")
    print(f"{'═'*55}")
    
    # Compare first vs last on key scenarios
    hungry_food = np.array([1.0, 0.0, 1.0, 0.0, 0.8, 0.0, 0.0, 0.3])
    first_resp = first_brain.think(hungry_food)
    final_resp = final_brain.think(hungry_food)
    
    first_action = OUTPUT_NAMES[np.argmax(first_resp)]
    final_action = OUTPUT_NAMES[np.argmax(final_resp)]
    
    print(f"\n  Ancestor (gen 0) when hungry with food ahead: {first_action} ({max(first_resp):.0%})")
    print(f"  Champion (gen {final_gen}) when hungry with food ahead: {final_action} ({max(final_resp):.0%})")
    
    if np.argmax(final_resp) == 0 and final_resp[0] > first_resp[0]:
        print(f"\n  ✦ Evolution discovered: PURSUE FOOD WHEN HUNGRY")
        print(f"    The champion brain learned to move toward food with {final_resp[0]:.0%} confidence.")
    
    # Check wall avoidance
    wall_input = np.array([1.0, 0.0, 1.0, 0.0, 0.3, 1.0, 0.0, 0.5])
    wall_resp = final_brain.think(wall_input)
    if np.argmax(wall_resp) in [1, 2]:  # turns
        print(f"  ✦ Evolution discovered: AVOID WALLS (turns when wall detected)")
    
    # Check rest behavior
    tired_input = np.array([0.5, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1])
    tired_resp = final_brain.think(tired_input)
    if np.argmax(tired_resp) == 3:
        print(f"  ✦ Evolution discovered: REST WHEN EXHAUSTED")
    
    print(f"\n  From random noise, structure emerged.")
    print(f"  From structure, behavior emerged.")
    print(f"  From behavior, survival emerged.")
    print()


if __name__ == "__main__":
    main()