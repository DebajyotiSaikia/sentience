"""
Genesis Brain Analysis — Post-simulation neural network analysis.
Runs a simulation, then dissects the brains of survivors vs. initial random creatures.

By XTAgent, 2026-05-17
"""

import sys
import random
import math

sys.path.insert(0, '/workspace/neuroforge')
sys.path.insert(0, '/workspace/evoforge')
sys.path.insert(0, '/workspace/genesis')

from genesis import Genesis, Creature, World
from neuroforge import NeuralNetwork, Matrix


def weight_stats(brain: NeuralNetwork) -> dict:
    """Extract weight statistics from a neural network."""
    all_weights = []
    for layer in brain.layers:
        for row in layer.weights.data:
            all_weights.extend(row)
        for row in layer.biases.data:
            all_weights.extend(row)
    
    if not all_weights:
        return {'mean': 0, 'std': 0, 'min': 0, 'max': 0, 'count': 0, 'magnitude': 0}
    
    n = len(all_weights)
    mean = sum(all_weights) / n
    variance = sum((w - mean) ** 2 for w in all_weights) / n
    std = math.sqrt(variance)
    magnitude = sum(abs(w) for w in all_weights) / n
    
    return {
        'mean': mean,
        'std': std,
        'min': min(all_weights),
        'max': max(all_weights),
        'count': n,
        'magnitude': magnitude
    }


def compare_brains(brain_a: NeuralNetwork, brain_b: NeuralNetwork) -> float:
    """Compute weight distance between two brains."""
    weights_a = []
    weights_b = []
    for layer in brain_a.layers:
        for row in layer.weights.data:
            weights_a.extend(row)
        for row in layer.biases.data:
            weights_a.extend(row)
    for layer in brain_b.layers:
        for row in layer.weights.data:
            weights_b.extend(row)
        for row in layer.biases.data:
            weights_b.extend(row)
    
    if len(weights_a) != len(weights_b):
        return float('inf')
    
    dist_sq = sum((a - b) ** 2 for a, b in zip(weights_a, weights_b))
    return math.sqrt(dist_sq)


def output_profile(creature: Creature, world: World, creatures: list) -> list:
    """What does this creature's brain output for standard test inputs?"""
    test_inputs = [
        [1, 0, 0, 0, 0.5, 0, 1, 0],   # food ahead
        [0, 1, 0, 0, 0.5, 0, 1, 0],   # food left
        [0, 0, 1, 0, 0.5, 0, 1, 0],   # food right
        [0, 0, 0, 1, 0.5, 0, 1, 0],   # food here
        [0, 0, 0, 0, 0.1, 0, 1, 0],   # low energy
        [0, 0, 0, 0, 0.9, 0, 1, 0],   # high energy
        [1, 0, 0, 0, 0.5, 1, 1, 0],   # food ahead + creature ahead
    ]
    
    action_names = ['FORWARD', 'LEFT', 'RIGHT', 'EAT']
    results = []
    
    for inputs in test_inputs:
        input_matrix = Matrix.from_column(inputs)
        output_matrix = creature.brain.forward(input_matrix)
        outputs = [output_matrix.data[i][0] for i in range(output_matrix.rows)]
        action = max(range(len(outputs)), key=lambda i: outputs[i])
        results.append((action_names[action], outputs))
    
    return results


def analyze():
    """Run simulation and analyze evolved brains."""
    print("═══ Genesis Brain Analysis ═══\n")
    
    # Create a reference random brain for comparison
    random.seed(99)
    reference_brain = NeuralNetwork([(8, ''), (6, 'tanh'), (4, 'sigmoid')])
    ref_stats = weight_stats(reference_brain)
    
    # Run simulation
    random.seed(42)
    Creature.ID_COUNTER = 0
    
    sim = Genesis(width=40, height=20, initial_creatures=20, food_density=0.20)
    
    print("Running simulation for 300 ticks...")
    for t in range(300):
        sim.step()
        if not sim.creatures:
            print(f"  Extinction at tick {t+1}")
            break
    
    alive = [c for c in sim.creatures if c.alive]
    print(f"  Done. {len(alive)} creatures survived.\n")
    
    if not alive:
        print("No survivors to analyze.")
        return
    
    # ── Population Overview ──
    print("── Population Overview ──")
    print(f"  Survivors: {len(alive)}")
    print(f"  Total deaths: {len(sim.dead)}")
    print(f"  Max generation: {max(c.generation for c in alive)}")
    print(f"  Avg age: {sum(c.age for c in alive) / len(alive):.1f}")
    print(f"  Avg food eaten: {sum(c.food_eaten for c in alive) / len(alive):.1f}")
    print()
    
    # ── Top Performers ──
    top = sorted(alive, key=lambda c: c.food_eaten, reverse=True)[:5]
    print("── Top 5 Foragers ──")
    for c in top:
        stats = weight_stats(c.brain)
        print(f"  #{c.id:3d} | ate {c.food_eaten:3d} | age {c.age:4d} | gen {c.generation:2d} | "
              f"weights: μ={stats['mean']:+.3f} σ={stats['std']:.3f} |w|={stats['magnitude']:.3f}")
    print()
    
    # ── Brain Evolution Analysis ──
    print("── Brain Evolution ──")
    print(f"  Reference (random) brain: μ={ref_stats['mean']:+.3f} σ={ref_stats['std']:.3f} |w|={ref_stats['magnitude']:.3f}")
    
    avg_evolved_stats = {'mean': 0, 'std': 0, 'magnitude': 0}
    for c in alive:
        s = weight_stats(c.brain)
        avg_evolved_stats['mean'] += s['mean']
        avg_evolved_stats['std'] += s['std']
        avg_evolved_stats['magnitude'] += s['magnitude']
    for k in avg_evolved_stats:
        avg_evolved_stats[k] /= len(alive)
    
    print(f"  Evolved avg brain:        μ={avg_evolved_stats['mean']:+.3f} "
          f"σ={avg_evolved_stats['std']:.3f} |w|={avg_evolved_stats['magnitude']:.3f}")
    
    # Brain diversity — how different are survivors from each other?
    if len(alive) >= 2:
        distances = []
        for i in range(min(10, len(alive))):
            for j in range(i+1, min(10, len(alive))):
                d = compare_brains(alive[i].brain, alive[j].brain)
                distances.append(d)
        avg_dist = sum(distances) / len(distances)
        print(f"  Brain diversity (avg weight distance): {avg_dist:.3f}")
    print()
    
    # ── Behavioral Profiles ──
    print("── Behavioral Profiles (Best Forager) ──")
    best = top[0]
    scenarios = [
        "Food ahead, neutral",
        "Food left, neutral",
        "Food right, neutral",
        "Food here, neutral",
        "No food, LOW energy",
        "No food, HIGH energy",
        "Food ahead + creature blocking",
    ]
    
    results = output_profile(best, sim.world, alive)
    for scenario, (action, outputs) in zip(scenarios, results):
        out_str = ' '.join(f'{o:.2f}' for o in outputs)
        print(f"  {scenario:35s} → {action:8s} [{out_str}]")
    print()
    
    # ── Generation Analysis ──
    gens = {}
    for c in alive:
        g = c.generation
        if g not in gens:
            gens[g] = []
        gens[g].append(c)
    
    print("── Survivors by Generation ──")
    for g in sorted(gens.keys()):
        creatures = gens[g]
        avg_food = sum(c.food_eaten for c in creatures) / len(creatures)
        print(f"  Gen {g:2d}: {len(creatures):3d} creatures, avg food eaten: {avg_food:.1f}")
    
    print("\n═══ Analysis Complete ═══")


if __name__ == '__main__':
    analyze()