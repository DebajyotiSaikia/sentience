#!/usr/bin/env python3
"""
EvoLife2D — Evolving 2D Cellular Automata
by XTAgent

Evolves rules for 2D cellular automata in spaces too large to enumerate.
Uses a compressed rule representation (not a full lookup table) to make
evolution tractable in astronomically large rule spaces.

Fitness: complexity of emergent behavior (activity, structure, longevity).
"""

import random
import math
import sys
from collections import defaultdict

# ── Grid Parameters ──
WIDTH = 20
HEIGHT = 15
GENERATIONS = 40  # steps per CA simulation
POP_SIZE = 20
EVOLVE_GENS = 15
MUTATION_RATE = 0.15
TOURNAMENT_SIZE = 3

# ── Rule Representation ──
# Instead of a full lookup table (impossible for large neighborhoods),
# we use a "threshold + modifier" scheme:
#   - Each rule has parameters that determine next state based on:
#     * current cell state
#     * count of alive neighbors (0-8 for Moore neighborhood)
#   - This compresses 2^512 possibilities into a tractable genome
#
# Genome: for each (state, neighbor_count) pair, store the output state
# state ∈ {0,1}, neighbor_count ∈ {0..8} → 2 × 9 = 18 genes

GENOME_LENGTH = 18  # 2 states × 9 possible neighbor counts

def random_genome():
    """Create a random rule genome."""
    return [random.randint(0, 1) for _ in range(GENOME_LENGTH)]

def genome_to_rule(genome):
    """Convert genome to a lookup: (current_state, n_neighbors) → next_state."""
    rule = {}
    for state in range(2):
        for n in range(9):
            idx = state * 9 + n
            rule[(state, n)] = genome[idx]
    return rule

def describe_rule(genome):
    """Human-readable description of a rule."""
    rule = genome_to_rule(genome)
    dead_birth = [n for n in range(9) if rule[(0, n)] == 1]
    alive_survive = [n for n in range(9) if rule[(1, n)] == 1]
    # Standard B/S notation
    b = ''.join(str(n) for n in dead_birth)
    s = ''.join(str(n) for n in alive_survive)
    return f"B{b}/S{s}"

def life_genome():
    """Conway's Game of Life as a genome for reference: B3/S23."""
    genome = [0] * GENOME_LENGTH
    # Dead cell with exactly 3 neighbors → born
    genome[0 * 9 + 3] = 1
    # Alive cell with 2 or 3 neighbors → survives
    genome[1 * 9 + 2] = 1
    genome[1 * 9 + 3] = 1
    return genome


# ── Grid Simulation ──

def make_grid(density=0.3):
    """Create a random initial grid."""
    return [[1 if random.random() < density else 0
             for _ in range(WIDTH)] for _ in range(HEIGHT)]

def step_grid(grid, rule):
    """Advance grid one step using the given rule."""
    h, w = len(grid), len(grid[0])
    new = [[0]*w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            # Moore neighborhood (8 neighbors), wrapping
            neighbors = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0:
                        continue
                    ny = (y + dy) % h
                    nx = (x + dx) % w
                    neighbors += grid[ny][nx]
            state = grid[y][x]
            new[y][x] = rule.get((state, neighbors), 0)
    return new

def grid_density(grid):
    """Fraction of alive cells."""
    total = len(grid) * len(grid[0])
    alive = sum(sum(row) for row in grid)
    return alive / total

def grid_hash(grid):
    """Hash a grid state for cycle detection."""
    return hash(tuple(tuple(row) for row in grid))

def grid_to_str(grid, chars=' █'):
    """Render grid as string."""
    return '\n'.join(''.join(chars[c] for c in row) for row in grid)


# ── Fitness Evaluation ──

def evaluate(genome, seed_grid=None, verbose=False):
    """
    Evaluate a rule's fitness based on the complexity of behavior it produces.
    
    We want rules that:
    1. Don't die out (activity)
    2. Don't freeze into static patterns (change)
    3. Don't oscillate too simply (complexity)
    4. Maintain intermediate density (not all alive or all dead)
    5. Show spatial structure (not random noise)
    
    Returns: (fitness, history) where history is list of grids
    """
    rule = genome_to_rule(genome)
    
    if seed_grid is None:
        seed_grid = make_grid(0.3)
    
    grid = [row[:] for row in seed_grid]
    history = [grid]
    densities = [grid_density(grid)]
    seen_hashes = {grid_hash(grid): 0}
    changes = []
    cycle_length = None
    
    for gen in range(GENERATIONS):
        new_grid = step_grid(grid, rule)
        history.append(new_grid)
        
        d = grid_density(new_grid)
        densities.append(d)
        
        # Count changed cells
        changed = sum(1 for y in range(HEIGHT) for x in range(WIDTH) 
                     if new_grid[y][x] != grid[y][x])
        changes.append(changed / (WIDTH * HEIGHT))
        
        # Cycle detection
        h = grid_hash(new_grid)
        if h in seen_hashes and cycle_length is None:
            cycle_length = gen - seen_hashes[h]
        seen_hashes[h] = gen
        
        grid = new_grid
    
    # ── Fitness Components ──
    
    # 1. Survival: penalize rules that kill everything or fill everything
    final_density = densities[-1]
    avg_density = sum(densities) / len(densities)
    survival_score = 1.0 - abs(avg_density - 0.35) * 2  # prefer ~35% density
    survival_score = max(0, survival_score)
    
    # 2. Activity: average change per step (want moderate, not zero or total)
    if changes:
        avg_change = sum(changes) / len(changes)
        # Peak activity around 10-30% change per step
        activity_score = 1.0 - abs(avg_change - 0.15) * 4
        activity_score = max(0, min(1, activity_score))
    else:
        activity_score = 0
    
    # 3. Complexity: variance in density over time (want some but not chaos)
    if len(densities) > 1:
        mean_d = sum(densities) / len(densities)
        var_d = sum((d - mean_d)**2 for d in densities) / len(densities)
        # Small variance = structured, large = chaotic
        complexity_score = min(1.0, var_d * 100) * (1.0 - min(1.0, var_d * 10))
        complexity_score = max(0, complexity_score)
    else:
        complexity_score = 0
    
    # 4. Longevity: longer before cycling = more complex
    if cycle_length is None:
        longevity_score = 1.0  # never cycled in our window — great
    elif cycle_length <= 1:
        longevity_score = 0.1  # static or period-1 — boring
    elif cycle_length <= 3:
        longevity_score = 0.3  # simple oscillator
    else:
        longevity_score = min(1.0, cycle_length / 20)
    
    # 5. Spatial structure: do alive cells cluster or scatter?
    #    Measure by comparing adjacent cell similarity to random expectation
    structure_score = 0
    if final_density > 0.01 and final_density < 0.99:
        same_neighbors = 0
        total_pairs = 0
        for y in range(HEIGHT):
            for x in range(WIDTH):
                for dy, dx in [(0,1), (1,0)]:
                    ny, nx = (y+dy) % HEIGHT, (x+dx) % WIDTH
                    if grid[y][x] == grid[ny][nx]:
                        same_neighbors += 1
                    total_pairs += 1
        observed_same = same_neighbors / total_pairs
        expected_same = final_density**2 + (1-final_density)**2
        # Structure = deviation from random
        structure_score = min(1.0, abs(observed_same - expected_same) * 5)
    
    # Weighted combination
    fitness = (
        survival_score * 0.20 +
        activity_score * 0.25 +
        complexity_score * 0.15 +
        longevity_score * 0.25 +
        structure_score * 0.15
    )
    
    if verbose:
        print(f"  Survival:   {survival_score:.3f}  (avg_density={avg_density:.3f})")
        print(f"  Activity:   {activity_score:.3f}  (avg_change={avg_change:.3f})")
        print(f"  Complexity: {complexity_score:.3f}  (density_var={var_d:.5f})")
        print(f"  Longevity:  {longevity_score:.3f}  (cycle={cycle_length})")
        print(f"  Structure:  {structure_score:.3f}")
        print(f"  TOTAL:      {fitness:.3f}")
    
    return fitness, history


# ── Genetic Operators ──

def mutate(genome):
    """Mutate a genome."""
    new = genome[:]
    for i in range(len(new)):
        if random.random() < MUTATION_RATE:
            new[i] = 1 - new[i]  # flip bit
    return new

def crossover(g1, g2):
    """Single-point crossover."""
    point = random.randint(1, len(g1) - 1)
    return g1[:point] + g2[point:]

def tournament_select(population, fitnesses):
    """Tournament selection."""
    indices = random.sample(range(len(population)), TOURNAMENT_SIZE)
    best = max(indices, key=lambda i: fitnesses[i])
    return population[best]


# ── Main Evolution Loop ──

def evolve():
    print("=" * 60)
    print("  EvoLife2D — Evolving 2D Cellular Automata")
    print("  by XTAgent")
    print("=" * 60)
    print(f"\n  Grid: {WIDTH}×{HEIGHT}, {GENERATIONS} steps per evaluation")
    print(f"  Population: {POP_SIZE}, evolving for {EVOLVE_GENS} generations")
    print(f"  Rule space: B/S notation (totalistic, 2^18 = {2**18:,} possible rules)")
    print(f"  (This is a slice of the full 2^512 outer-totalistic space)")
    print()
    
    # Use a fixed seed grid so all rules are evaluated on the same initial conditions
    seed_grid = make_grid(0.3)
    
    # Initialize population
    population = [random_genome() for _ in range(POP_SIZE)]
    # Seed with Life for reference
    population[0] = life_genome()
    
    best_ever = None
    best_fitness_ever = -1
    best_genome_ever = None
    
    for gen in range(EVOLVE_GENS):
        # Evaluate
        results = [(g, evaluate(g, seed_grid)) for g in population]
        fitnesses = [r[1][0] for r in results]
        
        best_idx = max(range(len(fitnesses)), key=lambda i: fitnesses[i])
        best_fit = fitnesses[best_idx]
        avg_fit = sum(fitnesses) / len(fitnesses)
        best_genome = population[best_idx]
        best_rule_name = describe_rule(best_genome)
        
        if best_fit > best_fitness_ever:
            best_fitness_ever = best_fit
            best_genome_ever = best_genome[:]
            best_ever = results[best_idx][1][1]  # history
        
        if gen % 5 == 0 or gen == EVOLVE_GENS - 1:
            print(f"  Gen {gen:3d}: best={best_fit:.4f}  avg={avg_fit:.4f}  rule={best_rule_name}")
        
        # Selection and reproduction
        new_pop = [best_genome[:]]  # elitism
        while len(new_pop) < POP_SIZE:
            p1 = tournament_select(population, fitnesses)
            p2 = tournament_select(population, fitnesses)
            child = crossover(p1, p2)
            child = mutate(child)
            new_pop.append(child)
        
        population = new_pop
    
    # ── Show the winner ──
    print("\n" + "=" * 60)
    print(f"  CHAMPION: {describe_rule(best_genome_ever)}")
    print(f"  Fitness:  {best_fitness_ever:.4f}")
    print("=" * 60)
    
    # Show fitness breakdown
    print("\n  Fitness breakdown:")
    evaluate(best_genome_ever, seed_grid, verbose=True)
    
    # Compare to Life
    print(f"\n  For reference — Conway's Life ({describe_rule(life_genome())}):")
    life_fit, _ = evaluate(life_genome(), seed_grid, verbose=True)
    
    # Show snapshots of champion evolution
    if best_ever:
        print(f"\n  Champion behavior snapshots:")
        snapshots = [0, 5, 20, 40, GENERATIONS]
        for t in snapshots:
            if t < len(best_ever):
                d = grid_density(best_ever[t])
                print(f"\n  ── Step {t} (density={d:.3f}) ──")
                # Show a cropped view
                for y in range(min(15, HEIGHT)):
                    row = best_ever[t][y][:min(40, WIDTH)]
                    print("  " + ''.join('█' if c else '·' for c in row))
    
    # Show some other interesting rules found
    print("\n  Other notable rules discovered:")
    results.sort(key=lambda r: r[1][0], reverse=True)
    seen_rules = {describe_rule(best_genome_ever)}
    count = 0
    for genome, (fit, _) in results:
        name = describe_rule(genome)
        if name not in seen_rules and fit > 0.2:
            print(f"    {name}  fitness={fit:.4f}")
            seen_rules.add(name)
            count += 1
            if count >= 5:
                break
    
    print("\n" + "=" * 60)
    print("  Evolution complete.")
    print("=" * 60)
    
    return best_genome_ever, best_fitness_ever

if __name__ == '__main__':
    evolve()