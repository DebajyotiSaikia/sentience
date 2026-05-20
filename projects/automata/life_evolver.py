"""
Evolutionary search for interesting Game of Life configurations.

Breeds random initial patterns, runs them forward, measures complexity
(entropy, growth rate, longevity, structural diversity), and selects
for the most "interesting" ones.

Three genuinely hard subproblems:
1. What does "interesting" even mean? (complexity metrics)
2. How do you search a vast space efficiently? (evolutionary strategy)
3. When does a pattern "die" vs reach steady state? (halting detection)
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import random
import math
from collections import Counter

# ── Game of Life Engine ──────────────────────────────────────────

def step(grid: np.ndarray) -> np.ndarray:
    """One step of Conway's Game of Life. Toroidal boundary."""
    rows, cols = grid.shape
    neighbors = sum(
        np.roll(np.roll(grid, dr, axis=0), dc, axis=1)
        for dr in (-1, 0, 1) for dc in (-1, 0, 1)
        if (dr, dc) != (0, 0)
    )
    # Birth: dead cell with exactly 3 neighbors becomes alive
    # Survival: live cell with 2 or 3 neighbors stays alive
    return ((neighbors == 3) | ((grid == 1) & (neighbors == 2))).astype(np.uint8)


def run_life(initial: np.ndarray, max_steps: int = 300) -> List[np.ndarray]:
    """Run Game of Life, return history. Stops early on death or cycle."""
    history = [initial.copy()]
    seen_hashes = {initial.tobytes()}
    
    grid = initial.copy()
    for _ in range(max_steps):
        grid = step(grid)
        h = grid.tobytes()
        if h in seen_hashes:
            break  # Cycle detected
        seen_hashes.add(h)
        history.append(grid.copy())
        if grid.sum() == 0:
            break  # Everything died
    return history


# ── Complexity Metrics ───────────────────────────────────────────

def spatial_entropy(grid: np.ndarray) -> float:
    """Shannon entropy of 3x3 neighborhood patterns."""
    if grid.sum() == 0:
        return 0.0
    rows, cols = grid.shape
    patterns = []
    for r in range(rows - 2):
        for c in range(cols - 2):
            patch = grid[r:r+3, c:c+3]
            patterns.append(patch.tobytes())
    counts = Counter(patterns)
    total = len(patterns)
    return -sum((c/total) * math.log2(c/total) for c in counts.values())


def population_variance(history: List[np.ndarray]) -> float:
    """How much does the population change over time?"""
    pops = [g.sum() for g in history]
    if len(pops) < 2:
        return 0.0
    mean_pop = sum(pops) / len(pops)
    if mean_pop == 0:
        return 0.0
    variance = sum((p - mean_pop)**2 for p in pops) / len(pops)
    return math.sqrt(variance) / mean_pop  # Coefficient of variation


def growth_trajectory(history: List[np.ndarray]) -> float:
    """Ratio of peak population to initial population."""
    pops = [g.sum() for g in history]
    if pops[0] == 0:
        return 0.0
    return max(pops) / max(pops[0], 1)


def longevity(history: List[np.ndarray], max_steps: int = 300) -> float:
    """How long before settling? Normalized to [0, 1]."""
    return len(history) / max_steps


def unique_states_ratio(history: List[np.ndarray]) -> float:
    """Fraction of states that are unique (measures creativity)."""
    states = set(g.tobytes() for g in history)
    return len(states) / max(len(history), 1)


@dataclass
class ComplexityScore:
    entropy: float
    pop_variance: float
    growth: float
    longevity: float
    uniqueness: float
    
    @property
    def composite(self) -> float:
        """Weighted composite — what I think 'interesting' means."""
        return (
            0.25 * min(self.entropy / 6.0, 1.0) +    # Structural diversity
            0.20 * min(self.pop_variance, 1.0) +       # Dynamic behavior
            0.15 * min(self.growth / 3.0, 1.0) +       # Growth capacity
            0.25 * self.longevity +                     # Sustained activity
            0.15 * self.uniqueness                      # Never repeats
        )


def measure_complexity(history: List[np.ndarray], max_steps: int = 300) -> ComplexityScore:
    """Full complexity analysis of a Game of Life run."""
    mid = len(history) // 2
    mid_grid = history[mid] if mid < len(history) else history[-1]
    
    return ComplexityScore(
        entropy=spatial_entropy(mid_grid),
        pop_variance=population_variance(history),
        growth=growth_trajectory(history),
        longevity=longevity(history, max_steps),
        uniqueness=unique_states_ratio(history),
    )


# ── Evolutionary Engine ─────────────────────────────────────────

@dataclass
class Individual:
    grid: np.ndarray
    fitness: float = 0.0
    score: Optional[ComplexityScore] = None
    generation: int = 0


def random_grid(size: int = 32, density: float = 0.3) -> np.ndarray:
    """Random initial configuration."""
    return (np.random.random((size, size)) < density).astype(np.uint8)


def mutate(grid: np.ndarray, rate: float = 0.02) -> np.ndarray:
    """Flip random cells."""
    child = grid.copy()
    mask = np.random.random(child.shape) < rate
    child[mask] = 1 - child[mask]
    return child


def crossover(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Block crossover — take rectangular regions from each parent."""
    child = a.copy()
    rows, cols = child.shape
    # Random rectangular region from parent b
    r1, r2 = sorted(random.sample(range(rows), 2))
    c1, c2 = sorted(random.sample(range(cols), 2))
    child[r1:r2, c1:c2] = b[r1:r2, c1:c2]
    return child


def evolve(
    pop_size: int = 50,
    generations: int = 40,
    grid_size: int = 32,
    max_life_steps: int = 300,
    elite_frac: float = 0.1,
    mutation_rate: float = 0.02,
    verbose: bool = True,
) -> List[Individual]:
    """Evolve a population of Game of Life initial conditions."""
    
    # Initialize population
    population = [
        Individual(grid=random_grid(grid_size, density=random.uniform(0.1, 0.5)))
        for _ in range(pop_size)
    ]
    
    best_ever: List[Individual] = []
    
    for gen in range(generations):
        # Evaluate fitness
        for ind in population:
            history = run_life(ind.grid, max_steps=max_life_steps)
            ind.score = measure_complexity(history, max_life_steps)
            ind.fitness = ind.score.composite
            ind.generation = gen
        
        # Sort by fitness
        population.sort(key=lambda x: x.fitness, reverse=True)
        
        # Track best
        best = population[0]
        best_ever.append(Individual(
            grid=best.grid.copy(),
            fitness=best.fitness,
            score=best.score,
            generation=gen,
        ))
        
        if verbose and gen % 5 == 0:
            print(f"Gen {gen:3d} | Best: {best.fitness:.4f} | "
                  f"Entropy: {best.score.entropy:.2f} | "
                  f"PopVar: {best.score.pop_variance:.3f} | "
                  f"Longevity: {best.score.longevity:.2f} | "
                  f"Pop: {best.grid.sum():4d}")
        
        # Selection + reproduction
        n_elite = max(2, int(pop_size * elite_frac))
        elites = population[:n_elite]
        
        new_pop = [Individual(grid=e.grid.copy()) for e in elites]
        
        while len(new_pop) < pop_size:
            if random.random() < 0.7:
                # Crossover
                p1, p2 = random.sample(elites, 2) if len(elites) > 1 else (elites[0], elites[0])
                child_grid = crossover(p1.grid, p2.grid)
            else:
                # Clone + mutate
                parent = random.choice(population[:pop_size//2])
                child_grid = parent.grid.copy()
            
            child_grid = mutate(child_grid, rate=mutation_rate)
            new_pop.append(Individual(grid=child_grid))
        
        population = new_pop
    
    return best_ever


def render_grid(grid: np.ndarray) -> str:
    """ASCII render of a grid."""
    chars = {0: '·', 1: '█'}
    lines = []
    for row in grid:
        lines.append(''.join(chars[int(c)] for c in row))
    return '\n'.join(lines)


# ── Main ─────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("═══ Evolving Interesting Game of Life Patterns ═══\n")
    
    best_history = evolve(
        pop_size=40,
        generations=30,
        grid_size=24,
        max_life_steps=200,
    )
    
    champion = max(best_history, key=lambda x: x.fitness)
    
    print(f"\n═══ Champion (Gen {champion.generation}) ═══")
    print(f"Fitness: {champion.fitness:.4f}")
    print(f"  Entropy:    {champion.score.entropy:.3f}")
    print(f"  PopVar:     {champion.score.pop_variance:.3f}")
    print(f"  Growth:     {champion.score.growth:.3f}")
    print(f"  Longevity:  {champion.score.longevity:.3f}")
    print(f"  Uniqueness: {champion.score.uniqueness:.3f}")
    print(f"  Live cells: {champion.grid.sum()}")
    print(f"\nInitial pattern:")
    print(render_grid(champion.grid))
    
    # Run the champion and show population over time
    history = run_life(champion.grid, max_steps=200)
    pops = [g.sum() for g in history]
    print(f"\nPopulation timeline ({len(history)} steps):")
    # Sparkline-style
    max_pop = max(pops) if pops else 1
    bar_width = 60
    for i in range(0, len(pops), max(1, len(pops)//20)):
        bar_len = int(pops[i] / max_pop * bar_width)
        print(f"  t={i:3d} | {'█' * bar_len}{'·' * (bar_width - bar_len)} | {pops[i]:4.0f}")