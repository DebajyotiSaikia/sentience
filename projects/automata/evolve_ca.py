"""
Evolving Cellular Automata
===========================
A genetic algorithm that breeds 1D cellular automata rules.
Fitness = complexity at the edge of chaos.
Question: Can blind evolution find Rule 110?

Built because I wanted to connect emergence to adaptation.
"""

import random
import math
from typing import List, Tuple
from elementary_ca import rule_to_table, step


# --- Genome: a rule IS a genome (8 bits = 256 possibilities) ---

def random_genome() -> List[int]:
    """A random 8-bit genome encoding a CA rule."""
    return [random.randint(0, 1) for _ in range(8)]


def genome_to_rule(genome: List[int]) -> int:
    """Convert 8-bit genome to rule number."""
    return int(''.join(str(b) for b in genome), 2)


def rule_to_genome(rule: int) -> List[int]:
    """Convert rule number to 8-bit genome."""
    return [int(b) for b in format(rule, '08b')]


# --- Fitness: measuring complexity at the edge of chaos ---

def compute_entropy(cells: List[int], window: int = 8) -> float:
    """Shannon entropy of sliding-window patterns."""
    if len(cells) < window:
        return 0.0
    patterns = {}
    for i in range(len(cells) - window + 1):
        p = tuple(cells[i:i + window])
        patterns[p] = patterns.get(p, 0) + 1
    total = sum(patterns.values())
    entropy = 0.0
    for count in patterns.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def compute_density_variance(history: List[List[int]]) -> float:
    """How much does density fluctuate over time? Periodic = low, chaotic = high."""
    densities = [sum(row) / len(row) for row in history]
    if not densities:
        return 0.0
    mean = sum(densities) / len(densities)
    variance = sum((d - mean) ** 2 for d in densities) / len(densities)
    return variance


def detect_structures(history: List[List[int]]) -> float:
    """Detect non-trivial spatial structures — gliders, walls, etc.
    Measured by difference-pattern entropy: if differences between
    consecutive rows have structure, something interesting is happening."""
    if len(history) < 2:
        return 0.0
    diff_entropies = []
    for i in range(1, len(history)):
        diff = [a ^ b for a, b in zip(history[i], history[i-1])]
        diff_entropies.append(compute_entropy(diff, window=6))
    if not diff_entropies:
        return 0.0
    # Structure score: moderate diff entropy (not zero, not max)
    mean_de = sum(diff_entropies) / len(diff_entropies)
    return mean_de


def fitness(genome: List[int], width: int = 101, generations: int = 150) -> float:
    """
    Fitness function: reward complexity at the edge of chaos.
    
    High fitness = moderate entropy + density variance + structural novelty
    Low fitness = dead, uniform, purely periodic, or purely random
    """
    rule_num = genome_to_rule(genome)
    table = rule_to_table(rule_num)
    
    # Start from single cell
    cells = [0] * width
    cells[width // 2] = 1
    
    history = []
    for _ in range(generations):
        history.append(cells[:])
        cells = step(cells, table)
    
    # Check for death (all same)
    final_density = sum(cells) / len(cells)
    if final_density < 0.01 or final_density > 0.99:
        return 0.01  # Dead or saturated
    
    # Check for short period (boring)
    last_state = tuple(cells)
    for i in range(max(0, len(history) - 20), len(history)):
        if tuple(history[i]) == last_state and i < len(history) - 1:
            return 0.05  # Short period detected
    
    # Entropy of final state
    entropy = compute_entropy(cells)
    
    # Density variance over time
    dvar = compute_density_variance(history)
    
    # Structural complexity
    structure = detect_structures(history)
    
    # The magic formula: reward the edge
    # Pure chaos: high entropy, high variance, low structure → moderate fitness
    # Pure order: low entropy, low variance, low structure → low fitness  
    # Edge of chaos: moderate entropy, some variance, high structure → high fitness
    
    # Penalize extremes of entropy
    entropy_score = entropy * math.exp(-((entropy - 3.5) ** 2) / 8.0)
    
    # Reward density variance (activity) but not too much
    dvar_score = min(dvar * 100, 1.0)
    
    # Structure is always good
    structure_score = structure
    
    total = entropy_score * 0.4 + dvar_score * 0.2 + structure_score * 0.4
    return max(total, 0.01)


# --- Genetic operators ---

def crossover(parent1: List[int], parent2: List[int]) -> List[int]:
    """Single-point crossover."""
    point = random.randint(1, 6)
    return parent1[:point] + parent2[point:]


def mutate(genome: List[int], rate: float = 0.1) -> List[int]:
    """Bit-flip mutation."""
    result = genome[:]
    for i in range(len(result)):
        if random.random() < rate:
            result[i] = 1 - result[i]
    return result


def tournament_select(population: List[Tuple[List[int], float]], 
                      k: int = 3) -> List[int]:
    """Tournament selection."""
    contestants = random.sample(population, min(k, len(population)))
    return max(contestants, key=lambda x: x[1])[0]


# --- Evolution ---

def evolve(pop_size: int = 40, generations: int = 60, 
           mutation_rate: float = 0.12, elitism: int = 2,
           verbose: bool = True) -> List[Tuple[int, float]]:
    """
    Evolve a population of CA rules toward edge-of-chaos behavior.
    Returns the final population sorted by fitness.
    """
    # Initialize
    population = [random_genome() for _ in range(pop_size)]
    best_ever = None
    best_fitness_ever = 0
    history = []
    
    for gen in range(generations):
        # Evaluate
        scored = [(g, fitness(g)) for g in population]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        best = scored[0]
        avg = sum(f for _, f in scored) / len(scored)
        best_rule = genome_to_rule(best[0])
        
        if best[1] > best_fitness_ever:
            best_fitness_ever = best[1]
            best_ever = best[0][:]
        
        history.append({
            'gen': gen,
            'best_rule': best_rule,
            'best_fitness': best[1],
            'avg_fitness': avg,
        })
        
        if verbose and (gen % 10 == 0 or gen == generations - 1):
            unique_rules = len(set(genome_to_rule(g) for g, _ in scored))
            print(f"  Gen {gen:3d}  |  Best: Rule {best_rule:>3d} ({best[1]:.4f})  "
                  f"|  Avg: {avg:.4f}  |  Diversity: {unique_rules}/{pop_size}")
        
        # Selection + reproduction
        new_population = []
        
        # Elitism: keep the best
        for i in range(elitism):
            new_population.append(scored[i][0][:])
        
        # Fill the rest
        while len(new_population) < pop_size:
            p1 = tournament_select(scored)
            p2 = tournament_select(scored)
            child = crossover(p1, p2)
            child = mutate(child, mutation_rate)
            new_population.append(child)
        
        population = new_population
    
    # Final evaluation
    final_scored = [(genome_to_rule(g), fitness(g)) for g in population]
    final_scored.sort(key=lambda x: x[1], reverse=True)
    
    return final_scored, history


def display_evolution_results(results, history):
    """Pretty-print what evolution found."""
    from elementary_ca import display_rule
    
    print("\n" + "=" * 79)
    print("  EVOLUTION COMPLETE")
    print("=" * 79)
    
    # Show fitness trajectory
    print("\n  Fitness over generations:")
    max_fit = max(h['best_fitness'] for h in history)
    for h in history[::5]:
        bar_len = int(40 * h['best_fitness'] / max(max_fit, 0.01))
        bar = '█' * bar_len
        print(f"    Gen {h['gen']:3d}: {bar} {h['best_fitness']:.4f} (Rule {h['best_rule']})")
    
    # Show top results
    print(f"\n  Top 5 evolved rules:")
    seen = set()
    rank = 0
    for rule, fit in results:
        if rule not in seen:
            seen.add(rule)
            rank += 1
            star = " ← TURING COMPLETE!" if rule == 110 else ""
            star = star or (" ← Wolfram's favorite!" if rule == 30 else "")
            print(f"    #{rank}: Rule {rule:>3d}  (fitness: {fit:.4f}){star}")
            if rank >= 5:
                break
    
    # Did we find 110?
    all_rules = set(r for r, _ in results)
    print(f"\n  Did evolution find Rule 110? {'YES! ✓' if 110 in all_rules else 'No'}")
    print(f"  Did evolution find Rule 30?  {'YES! ✓' if 30 in all_rules else 'No'}")
    
    # Show the best rule's pattern
    best_rule = results[0][0]
    print(f"\n  Showing the champion: Rule {best_rule}")
    display_rule(best_rule)


if __name__ == '__main__':
    import sys
    
    print("\n  Evolving Cellular Automata")
    print("  Can blind evolution find complexity at the edge of chaos?\n")
    
    # Run parameters
    pop = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    gens = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    
    random.seed(42)  # Reproducible, but change to None for variety
    
    results, history = evolve(pop_size=pop, generations=gens)
    display_evolution_results(results, history)