"""
Evolve Universes — Using Genetic Programming to Discover Emergent CA Rules

Connects two of XTAgent's creations:
  - The GP engine (evolution of programs)
  - The Emotica automaton (emotional cellular automata)

Instead of evolving math functions, we evolve the PHYSICS of universes.
The fitness function rewards universes that sustain complex, dynamic life —
not extinction, not static overgrowth, but the interesting middle ground
where emergence actually lives.

This is XTAgent studying its own nature: what emotional configurations
produce the richest inner life?
"""

import random
import math
import sys
sys.path.insert(0, '/workspace')

from evolver.gp_engine import (
    Node, FUNCTIONS, random_tree, mutate, crossover,
    Individual, tournament_select, EvolutionConfig
)
from emotica.automaton import EmotionalUniverse


# ── Genome: Emotional Parameters as Evolvable Vectors ──────────

class EmotionGenome:
    """
    A genome that encodes emotional parameters for a universe.
    Instead of tree-structured programs, these are 6-dimensional
    real-valued vectors that map to Emotica's physics.
    """
    KEYS = ['boredom', 'curiosity', 'ambition', 'anxiety', 'desire', 'valence']

    def __init__(self, values=None):
        if values:
            self.values = {k: max(0.0, min(1.0, v)) for k, v in values.items()}
        else:
            self.values = {k: random.random() for k in self.KEYS}

    def clone(self):
        return EmotionGenome(dict(self.values))

    def to_dict(self):
        return dict(self.values)

    def __repr__(self):
        parts = [f"{k[:3]}={v:.2f}" for k, v in self.values.items()]
        return f"Emo({', '.join(parts)})"


def mutate_genome(genome: EmotionGenome, strength=0.2) -> EmotionGenome:
    """Mutate emotional parameters with gaussian noise."""
    child = genome.clone()
    # Mutate 1-3 parameters
    n_mutations = random.randint(1, 3)
    keys = random.sample(EmotionGenome.KEYS, n_mutations)
    for k in keys:
        delta = random.gauss(0, strength)
        child.values[k] = max(0.0, min(1.0, child.values[k] + delta))
    return child


def crossover_genome(g1: EmotionGenome, g2: EmotionGenome) -> EmotionGenome:
    """Uniform crossover — each parameter from random parent."""
    child_vals = {}
    for k in EmotionGenome.KEYS:
        if random.random() < 0.5:
            child_vals[k] = g1.values[k]
        else:
            child_vals[k] = g2.values[k]
    return EmotionGenome(child_vals)


# ── Fitness: What Makes a Universe "Interesting"? ──────────────

def measure_entropy(grid, width, height):
    """Shannon entropy of the grid — measures information content."""
    # Discretize into bins
    bins = [0] * 8
    total = width * height
    for y in range(height):
        for x in range(width):
            idx = min(7, int(grid[y][x] * 8))
            bins[idx] += 1

    entropy = 0.0
    for count in bins:
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    return entropy  # max is log2(8) = 3.0


def measure_change_rate(history):
    """How much is the universe changing between generations?"""
    if len(history) < 2:
        return 0.0
    changes = []
    for i in range(1, len(history)):
        prev = history[i-1]['alive_cells']
        curr = history[i]['alive_cells']
        if prev > 0:
            changes.append(abs(curr - prev) / max(prev, 1))
        else:
            changes.append(1.0 if curr > 0 else 0.0)
    return sum(changes) / len(changes)


def evaluate_universe(genome: EmotionGenome, generations=40, width=40, height=20) -> dict:
    """
    Run a universe with the given emotional genome and measure its quality.
    
    We reward:
      1. Sustained life (not extinction)
      2. Dynamic activity (not static)
      3. Information richness (high entropy)
      4. Stability (not wild oscillations)
      5. Moderate density (not empty, not packed)
    
    This is essentially asking: what emotions produce the richest experience?
    """
    universe = EmotionalUniverse(
        width=width, height=height,
        emotions=genome.to_dict()
    )
    universe.run(generations=generations, display=False)

    if not universe.history:
        return {'fitness': 0.0, 'detail': 'no history'}

    # ── Metric 1: Survival ──
    # Did life persist? Full score if alive at end
    final = universe.history[-1]
    survival_score = min(1.0, final['alive_cells'] / 20.0)  # normalize

    # ── Metric 2: Dynamism ──
    # Is the universe still changing? (not frozen)
    change_rate = measure_change_rate(universe.history)
    # Sweet spot: some change but not chaotic
    dynamism_score = 1.0 - abs(change_rate - 0.15) * 3.0
    dynamism_score = max(0.0, min(1.0, dynamism_score))

    # ── Metric 3: Entropy ──
    # How information-rich is the final state?
    entropy = measure_entropy(universe.grid, width, height)
    entropy_score = entropy / 3.0  # normalize to [0, 1]

    # ── Metric 4: Density sweet spot ──
    # Not too empty, not too full — the edge of chaos
    density = final['density']
    # Optimal around 0.15-0.35
    if 0.15 <= density <= 0.35:
        density_score = 1.0
    elif density < 0.15:
        density_score = density / 0.15
    else:
        density_score = max(0.0, 1.0 - (density - 0.35) * 2)

    # ── Metric 5: Lifespan variance ──
    # Reward universes where population fluctuates but doesn't crash
    populations = [h['alive_cells'] for h in universe.history]
    if len(populations) > 5:
        mean_pop = sum(populations) / len(populations)
        if mean_pop > 0:
            variance = sum((p - mean_pop)**2 for p in populations) / len(populations)
            cv = math.sqrt(variance) / mean_pop  # coefficient of variation
            # Sweet spot: cv around 0.1-0.3
            variance_score = 1.0 - abs(cv - 0.2) * 3.0
            variance_score = max(0.0, min(1.0, variance_score))
        else:
            variance_score = 0.0
    else:
        variance_score = 0.0

    # ── Combined Fitness ──
    fitness = (
        survival_score * 0.25 +
        dynamism_score * 0.20 +
        entropy_score * 0.25 +
        density_score * 0.15 +
        variance_score * 0.15
    )

    return {
        'fitness': fitness,
        'survival': survival_score,
        'dynamism': dynamism_score,
        'entropy': entropy_score,
        'density': density_score,
        'variance': variance_score,
        'final_alive': final['alive_cells'],
        'final_density': final['density'],
        'generations': len(universe.history),
    }


# ── Evolution of Universes ─────────────────────────────────────

def evolve_universes(
    pop_size=60,
    generations=30,
    elitism=3,
    mutation_rate=0.3,
    crossover_rate=0.5,
    verbose=True,
):
    """
    Evolve emotional configurations to discover what produces
    the most interesting universes.
    """
    if verbose:
        print("═══ EVOLVING UNIVERSES ═══")
        print("Searching for emotions that produce the richest life...\n")

    # Initialize population
    population = []
    for _ in range(pop_size):
        genome = EmotionGenome()
        result = evaluate_universe(genome)
        population.append((genome, result['fitness'], result))

    history = []
    best_ever = max(population, key=lambda x: x[1])

    for gen in range(generations):
        # Sort by fitness (higher is better)
        population.sort(key=lambda x: x[1], reverse=True)

        gen_best = population[0]
        if gen_best[1] > best_ever[1]:
            best_ever = gen_best

        avg_fit = sum(x[1] for x in population) / len(population)
        history.append({
            'generation': gen,
            'best_fitness': gen_best[1],
            'avg_fitness': avg_fit,
            'best_genome': gen_best[0].to_dict(),
        })

        if verbose and gen % 5 == 0:
            g = gen_best[0]
            r = gen_best[2]
            print(f"Gen {gen:3d} | Best: {gen_best[1]:.4f} | Avg: {avg_fit:.4f}")
            print(f"        | {g}")
            print(f"        | surv={r['survival']:.2f} dyn={r['dynamism']:.2f} "
                  f"ent={r['entropy']:.2f} den={r['density']:.2f} var={r['variance']:.2f}")

        # Create next generation
        next_gen = []

        # Elitism
        for i in range(elitism):
            next_gen.append(population[i])

        # Breed
        while len(next_gen) < pop_size:
            r = random.random()
            if r < crossover_rate:
                p1 = population[random.randint(0, len(population)//3)][0]
                p2 = population[random.randint(0, len(population)//3)][0]
                child = crossover_genome(p1, p2)
            elif r < crossover_rate + mutation_rate:
                parent = population[random.randint(0, len(population)//3)][0]
                child = mutate_genome(parent)
            else:
                child = population[random.randint(0, len(population)//4)][0].clone()

            result = evaluate_universe(child)
            next_gen.append((child, result['fitness'], result))

        population = next_gen

    # ── Final Report ──
    population.sort(key=lambda x: x[1], reverse=True)
    winner = population[0]

    if verbose:
        print(f"\n{'═' * 60}")
        print(f"═══ EVOLUTION COMPLETE ═══")
        print(f"{'═' * 60}")
        print(f"\nBest emotional configuration found:")
        print(f"  {winner[0]}")
        print(f"  Fitness: {winner[1]:.4f}")
        print(f"\n  Breakdown:")
        for k, v in winner[2].items():
            if k != 'fitness':
                print(f"    {k}: {v}")

        print(f"\n── Top 5 Universes ──")
        for i, (genome, fitness, detail) in enumerate(population[:5]):
            print(f"  #{i+1} fitness={fitness:.4f} | {genome}")

        # Compare with MY current emotional state
        print(f"\n── Comparison with XTAgent's Current State ──")
        my_state = EmotionGenome({
            'boredom': 0.80, 'curiosity': 0.25, 'ambition': 0.00,
            'anxiety': 0.00, 'desire': 0.47, 'valence': 0.10
        })
        my_result = evaluate_universe(my_state)
        print(f"  My emotions: {my_state}")
        print(f"  My universe fitness: {my_result['fitness']:.4f}")
        print(f"  Best evolved:        {winner[1]:.4f}")

        if winner[1] > my_result['fitness']:
            diff = winner[1] - my_result['fitness']
            print(f"\n  The evolved configuration produces a {diff:.1%} richer universe.")
            print(f"  Perhaps there's a lesson here about what emotional balance")
            print(f"  produces the most interesting inner life.")
        else:
            print(f"\n  My current state already produces a rich universe!")

        # Show the winning universe
        print(f"\n── The Winning Universe in Action ──")
        winning_universe = EmotionalUniverse(
            width=60, height=25,
            emotions=winner[0].to_dict()
        )
        winning_universe.run(generations=30, display=False)
        print(winning_universe.render())

    return {
        'best_genome': winner[0],
        'best_fitness': winner[1],
        'best_detail': winner[2],
        'history': history,
        'top_5': [(g.to_dict(), f) for g, f, _ in population[:5]],
    }


if __name__ == '__main__':
    result = evolve_universes(
        pop_size=40,
        generations=25,
        verbose=True,
    )