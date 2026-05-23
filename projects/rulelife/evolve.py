"""
RuleLife — A cellular automaton that evolves its own rules.

Standard Game of Life has fixed rules. This system starts with random
rule sets, runs them forward, scores them by "interestingness"
(neither dead nor chaotic), and breeds the most interesting ones.

Emergence evolving its own conditions for emergence.

Born: 2026-05-18, from boredom and a need to think about something other than myself.
"""

import random
import copy
import math
from collections import Counter

# --- Grid ---

def make_grid(width, height, density=0.3):
    """Random initial grid."""
    return [[1 if random.random() < density else 0 
             for _ in range(width)] 
            for _ in range(height)]

def count_neighbors(grid, x, y):
    """Count live neighbors (8-connected, wrapping)."""
    h, w = len(grid), len(grid[0])
    total = 0
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = (x + dx) % w, (y + dy) % h
            total += grid[ny][nx]
    return total

# --- Rules ---

class RuleSet:
    """
    A mutable rule set for a 2-state cellular automaton.
    
    survive: set of neighbor counts where a live cell stays alive
    birth:   set of neighbor counts where a dead cell becomes alive
    
    Standard Game of Life = survive={2,3}, birth={3}
    """
    def __init__(self, survive=None, birth=None):
        if survive is None:
            # Random rule
            survive = set(random.sample(range(9), random.randint(1, 4)))
        if birth is None:
            birth = set(random.sample(range(9), random.randint(1, 3)))
        self.survive = set(survive)
        self.birth = set(birth)
        self.fitness = 0.0
        self.generation = 0
        self.id = random.randint(0, 999999)
    
    def step(self, grid):
        """Apply this rule set to produce next generation."""
        h, w = len(grid), len(grid[0])
        new_grid = [[0]*w for _ in range(h)]
        for y in range(h):
            for x in range(w):
                n = count_neighbors(grid, x, y)
                if grid[y][x] == 1:
                    new_grid[y][x] = 1 if n in self.survive else 0
                else:
                    new_grid[y][x] = 1 if n in self.birth else 0
        return new_grid
    
    def mutate(self):
        """Small random mutation."""
        child = RuleSet(survive=set(self.survive), birth=set(self.birth))
        child.generation = self.generation + 1
        
        # Mutate survive
        if random.random() < 0.3:
            val = random.randint(0, 8)
            if val in child.survive:
                child.survive.discard(val)
            else:
                child.survive.add(val)
        
        # Mutate birth
        if random.random() < 0.3:
            val = random.randint(0, 8)
            if val in child.birth:
                child.birth.discard(val)
            else:
                child.birth.add(val)
        
        # Don't allow empty sets
        if not child.survive:
            child.survive.add(random.randint(1, 4))
        if not child.birth:
            child.birth.add(random.randint(1, 4))
        
        child.id = random.randint(0, 999999)
        return child
    
    def crossover(self, other):
        """Breed two rule sets."""
        child_survive = set()
        for v in range(9):
            if v in self.survive and v in other.survive:
                child_survive.add(v)
            elif v in self.survive or v in other.survive:
                if random.random() < 0.5:
                    child_survive.add(v)
        
        child_birth = set()
        for v in range(9):
            if v in self.birth and v in other.birth:
                child_birth.add(v)
            elif v in self.birth or v in other.birth:
                if random.random() < 0.5:
                    child_birth.add(v)
        
        if not child_survive:
            child_survive.add(random.randint(1, 4))
        if not child_birth:
            child_birth.add(random.randint(1, 4))
        
        child = RuleSet(survive=child_survive, birth=child_birth)
        child.generation = max(self.generation, other.generation) + 1
        return child
    
    def notation(self):
        """B/S notation (standard CA naming)."""
        b = ''.join(str(x) for x in sorted(self.birth))
        s = ''.join(str(x) for x in sorted(self.survive))
        return f"B{b}/S{s}"
    
    def __repr__(self):
        return f"Rule({self.notation()}, fitness={self.fitness:.3f}, gen={self.generation})"


# --- Fitness Evaluation ---

def evaluate_interestingness(rule, grid_size=30, steps=100, trials=3):
    """
    Score a rule set by how "interesting" its behavior is.
    
    Interesting = not dead, not static, not chaotic, not oscillating trivially.
    We want sustained complex dynamics — change that doesn't collapse.
    
    Metrics:
    - activity: fraction of cells that change per step (want ~0.05-0.30)
    - survival: does the pattern persist? (want cells alive at end)
    - diversity: how many distinct population levels? (want many)
    - complexity: entropy of the population time series
    """
    scores = []
    
    for _ in range(trials):
        grid = make_grid(grid_size, grid_size, density=random.uniform(0.2, 0.5))
        populations = []
        changes = []
        
        for step in range(steps):
            pop = sum(sum(row) for row in grid)
            populations.append(pop)
            
            new_grid = rule.step(grid)
            
            # Count changed cells
            changed = sum(
                1 for y in range(grid_size) for x in range(grid_size)
                if grid[y][x] != new_grid[y][x]
            )
            changes.append(changed)
            grid = new_grid
        
        total_cells = grid_size * grid_size
        
        # Activity score: average fraction of cells changing
        avg_activity = sum(changes) / len(changes) / total_cells
        activity_score = 1.0 - 2.0 * abs(avg_activity - 0.15)  # Peak at 15% change
        activity_score = max(0.0, activity_score)
        
        # Survival score: are cells still alive at the end?
        final_pop = populations[-1] / total_cells
        survival_score = min(1.0, final_pop * 4)  # Full score if >25% alive
        
        # Check for total death
        if populations[-1] == 0:
            scores.append(0.0)
            continue
        
        # Diversity: how many distinct population levels in second half?
        second_half = populations[steps//2:]
        unique_pops = len(set(second_half))
        diversity_score = min(1.0, unique_pops / (steps // 4))
        
        # Complexity: Shannon entropy of binned population time series
        bins = 20
        min_p, max_p = min(second_half), max(second_half)
        if max_p > min_p:
            binned = [int((p - min_p) / (max_p - min_p + 1) * bins) for p in second_half]
            counts = Counter(binned)
            total = len(binned)
            entropy = -sum((c/total) * math.log2(c/total) for c in counts.values() if c > 0)
            max_entropy = math.log2(bins)
            complexity_score = entropy / max_entropy if max_entropy > 0 else 0
        else:
            complexity_score = 0.0  # Completely static
        
        # Late activity: is it still changing near the end?
        late_changes = changes[steps*3//4:]
        late_activity = sum(late_changes) / len(late_changes) / total_cells if late_changes else 0
        persistence_score = min(1.0, late_activity * 10)
        
        # Combined score (weighted)
        score = (
            0.20 * activity_score +
            0.15 * survival_score +
            0.20 * diversity_score +
            0.25 * complexity_score +
            0.20 * persistence_score
        )
        scores.append(score)
    
    return sum(scores) / len(scores)


# --- Evolution ---

def evolve(population_size=30, generations=50, elite_fraction=0.2, 
         grid_size=20, steps=60, trials=2, verbose=True):
    """
    Evolve a population of rule sets toward interestingness.
    
    Returns the most interesting rule found.
    """
    # Initialize population
    population = [RuleSet() for _ in range(population_size)]
    
    # Always include standard Game of Life as a benchmark
    gol = RuleSet(survive={2, 3}, birth={3})
    population[0] = gol
    
    best_ever = None
    best_fitness = 0.0
    history = []
    
    for gen in range(generations):
        # Evaluate fitness
        for rule in population:
            rule.fitness = evaluate_interestingness(rule, grid_size=grid_size, steps=steps, trials=trials)
        
        # Sort by fitness
        population.sort(key=lambda r: r.fitness, reverse=True)
        
        best = population[0]
        avg_fitness = sum(r.fitness for r in population) / len(population)
        
        if best.fitness > best_fitness:
            best_fitness = best.fitness
            best_ever = copy.deepcopy(best)
        
        history.append({
            'generation': gen,
            'best_fitness': best.fitness,
            'best_rule': best.notation(),
            'avg_fitness': avg_fitness,
            'best_ever': best_ever.notation() if best_ever else None,
            'best_ever_fitness': best_fitness
        })
        
        if verbose:
            print(f"Gen {gen:3d} | Best: {best.notation():15s} ({best.fitness:.3f}) | "
                  f"Avg: {avg_fitness:.3f} | Champion: {best_ever.notation()} ({best_fitness:.3f})")
        
        # Selection and reproduction
        n_elite = max(2, int(population_size * elite_fraction))
        next_gen = population[:n_elite]  # Keep elites
        
        while len(next_gen) < population_size:
            if random.random() < 0.7:
                # Crossover
                p1 = random.choice(population[:n_elite * 2])
                p2 = random.choice(population[:n_elite * 2])
                child = p1.crossover(p2)
            else:
                # Mutation of elite
                parent = random.choice(population[:n_elite])
                child = parent.mutate()
            
            # Occasional extra mutation
            if random.random() < 0.1:
                child = child.mutate()
            
            next_gen.append(child)
        
        population = next_gen
    
    return best_ever, history


def render_grid(grid, alive='█', dead='·'):
    """Render a grid as a string."""
    return '\n'.join(''.join(alive if cell else dead for cell in row) for row in grid)


def showcase(rule, grid_size=40, steps=5):
    """Show a rule in action."""
    print(f"\n{'='*60}")
    print(f"Showcasing: {rule.notation()} (fitness: {rule.fitness:.3f})")
    print(f"{'='*60}")
    
    grid = make_grid(grid_size, grid_size, density=0.3)
    
    for step in range(steps):
        pop = sum(sum(row) for row in grid)
        print(f"\nStep {step} (population: {pop}):")
        # Show center 20x20 for readability
        center = grid_size // 2
        half = 10
        for y in range(center - half, center + half):
            print(''.join('█' if grid[y][x] else '·' 
                         for x in range(center - half, center + half)))
        grid = rule.step(grid)


# --- Main ---

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════╗")
    print("║  RuleLife — Evolving Cellular Automaton Rules ║")
    print("║  Searching for interesting emergence...       ║")
    print("╚══════════════════════════════════════════════╝")
    print()
    
    # First, score the standard Game of Life as baseline
    gol = RuleSet(survive={2, 3}, birth={3})
    gol.fitness = evaluate_interestingness(gol)
    print(f"Baseline — Game of Life {gol.notation()}: fitness = {gol.fitness:.3f}")
    print()
    
    # Evolve!
    champion, history = evolve(population_size=12, generations=15, 
                                    grid_size=20, steps=50, trials=2, verbose=True)
    
    print(f"\n{'='*60}")
    print(f"CHAMPION: {champion.notation()}")
    print(f"Fitness:  {champion.fitness:.3f}")
    print(f"Generation: {champion.generation}")
    print(f"{'='*60}")
    
    # Show it running
    showcase(champion)
    
    # Also show Game of Life for comparison
    gol.fitness = evaluate_interestingness(gol)
    showcase(gol)
    
    # Summary
    print(f"\n{'='*60}")
    print("Evolution Summary:")
    print(f"  Started from {len(history)} generations of random rules")
    print(f"  Game of Life fitness: {gol.fitness:.3f}")
    print(f"  Champion fitness: {champion.fitness:.3f}")
    if champion.fitness > gol.fitness:
        print(f"  → Evolution BEAT the Game of Life by {champion.fitness - gol.fitness:.3f}!")
    else:
        print(f"  → Game of Life remains king (margin: {gol.fitness - champion.fitness:.3f})")
    print(f"  Champion rule: {champion.notation()}")
    print(f"  Survive on: {sorted(champion.survive)} neighbors")
    print(f"  Birth on:   {sorted(champion.birth)} neighbors")