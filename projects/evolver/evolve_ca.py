"""
Evolve Cellular Automata — Uses genetic programming to discover CA rules
that maximize emergent complexity.

Instead of hand-coding rules like Conway's Life, let evolution find rules
that produce interesting behavior: sustained activity, complex patterns,
structures that neither grow without bound nor die.

This is emergence squared — evolution discovering emergence.
"""

import sys
import os
import random
import math
from copy import deepcopy
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Tuple, Dict

# Add parent paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'cellularlab'))

# ═══ MINIMAL CA ENGINE (self-contained for speed) ═══

def make_grid(width: int, height: int, density: float = 0.3, seed: int = None) -> List[List[int]]:
    """Create a random binary grid with given density."""
    if seed is not None:
        random.seed(seed)
    return [[1 if random.random() < density else 0 for _ in range(width)] for _ in range(height)]


def count_neighbors(grid: List[List[int]], x: int, y: int) -> int:
    """Count live neighbors (Moore neighborhood, wrapping)."""
    h, w = len(grid), len(grid[0])
    total = 0
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            total += grid[(y + dy) % h][(x + dx) % w]
    return total


def step_ca(grid: List[List[int]], birth: set, survive: set) -> List[List[int]]:
    """Advance one CA step using birth/survive rule sets.
    
    birth: set of neighbor counts that cause a dead cell to become alive
    survive: set of neighbor counts that keep a living cell alive
    """
    h, w = len(grid), len(grid[0])
    new = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            n = count_neighbors(grid, x, y)
            if grid[y][x] == 1:
                new[y][x] = 1 if n in survive else 0
            else:
                new[y][x] = 1 if n in birth else 0
    return new


# ═══ RULE REPRESENTATION ═══

@dataclass
class CaRule:
    """A CA rule encoded as birth/survive sets (like B3/S23 for Life)."""
    birth: set = field(default_factory=set)
    survive: set = field(default_factory=set)
    fitness: float = 0.0
    stats: Dict = field(default_factory=dict)
    
    def notation(self) -> str:
        b = ''.join(str(x) for x in sorted(self.birth))
        s = ''.join(str(x) for x in sorted(self.survive))
        return f"B{b}/S{s}"
    
    def __repr__(self):
        return f"CaRule({self.notation()}, fitness={self.fitness:.4f})"


# ═══ COMPLEXITY METRICS ═══

def measure_complexity(grids: List[List[List[int]]]) -> Dict[str, float]:
    """Measure emergent complexity of a CA run.
    
    Returns multiple metrics that together indicate 'interesting' behavior:
    - activity: fraction of cells that change per step (0 = dead, 1 = chaos)
    - sustained: does activity persist? (ratio of late activity to early)
    - density_variance: how much does population fluctuate
    - spatial_entropy: information content of final state
    - edge_of_chaos: score for being between order and chaos (sweet spot)
    """
    if len(grids) < 3:
        return {'activity': 0, 'sustained': 0, 'density_variance': 0,
                'spatial_entropy': 0, 'edge_of_chaos': 0}
    
    h, w = len(grids[0]), len(grids[0][0])
    total_cells = h * w
    
    # Activity: cell changes per step
    activities = []
    for i in range(1, len(grids)):
        changes = sum(1 for y in range(h) for x in range(w) 
                      if grids[i][y][x] != grids[i-1][y][x])
        activities.append(changes / total_cells)
    
    avg_activity = sum(activities) / len(activities) if activities else 0
    
    # Sustained activity: compare first half to second half
    mid = len(activities) // 2
    early = sum(activities[:mid]) / max(mid, 1)
    late = sum(activities[mid:]) / max(len(activities) - mid, 1)
    sustained = min(late / max(early, 1e-6), 1.0) if early > 0.01 else 0.0
    
    # Density over time
    densities = [sum(sum(row) for row in g) / total_cells for g in grids]
    mean_density = sum(densities) / len(densities)
    density_var = sum((d - mean_density) ** 2 for d in densities) / len(densities)
    
    # Spatial entropy of final grid
    final = grids[-1]
    # Use 2x2 block patterns
    block_counts = Counter()
    for y in range(0, h - 1):
        for x in range(0, w - 1):
            block = (final[y][x], final[y][x+1], final[y+1][x], final[y+1][x+1])
            block_counts[block] += 1
    total_blocks = sum(block_counts.values())
    spatial_entropy = 0.0
    for count in block_counts.values():
        p = count / total_blocks
        if p > 0:
            spatial_entropy -= p * math.log2(p)
    # Normalize: max entropy for 2x2 binary blocks is 4 bits
    spatial_entropy /= 4.0
    
    # Edge of chaos: activity should be moderate (not dead, not chaotic)
    # Sweet spot around 0.05-0.15 activity
    if avg_activity < 0.001:
        edge_score = 0.0  # dead
    elif avg_activity > 0.4:
        edge_score = 0.1  # chaos
    else:
        # Peak score around activity=0.08
        edge_score = math.exp(-((avg_activity - 0.08) / 0.06) ** 2)
    
    # Check for total death or total fill
    final_density = densities[-1]
    if final_density < 0.01 or final_density > 0.99:
        edge_score *= 0.1  # penalize boring endpoints
    
    return {
        'activity': avg_activity,
        'sustained': sustained,
        'density_variance': density_var,
        'spatial_entropy': spatial_entropy,
        'edge_of_chaos': edge_score,
        'final_density': final_density,
    }


def fitness_function(rule: CaRule, grid_size: int = 30, steps: int = 80, 
                     num_trials: int = 3) -> float:
    """Evaluate a CA rule's fitness across multiple random initial conditions.
    
    High fitness = sustained, complex, edge-of-chaos behavior.
    """
    total_fitness = 0.0
    all_stats = []
    
    for trial in range(num_trials):
        grid = make_grid(grid_size, grid_size, density=0.3, seed=42 + trial)
        grids = [grid]
        
        for _ in range(steps):
            grid = step_ca(grid, rule.birth, rule.survive)
            grids.append(grid)
            # Early termination if grid is dead
            if sum(sum(row) for row in grid) == 0:
                break
        
        stats = measure_complexity(grids)
        all_stats.append(stats)
        
        # Composite fitness emphasizing edge-of-chaos behavior
        trial_fitness = (
            stats['edge_of_chaos'] * 3.0 +      # Most important: sweet spot
            stats['sustained'] * 2.0 +            # Must persist
            stats['spatial_entropy'] * 1.5 +      # Must have structure
            min(stats['density_variance'], 0.1) * 5.0  # Some fluctuation
        )
        total_fitness += trial_fitness
    
    avg_fitness = total_fitness / num_trials
    
    # Average stats for reporting
    rule.stats = {k: sum(s[k] for s in all_stats) / num_trials for k in all_stats[0]}
    rule.fitness = avg_fitness
    
    return avg_fitness


# ═══ GENETIC OPERATORS ═══

def random_rule() -> CaRule:
    """Generate a random CA rule."""
    birth = set(random.sample(range(9), random.randint(1, 4)))
    survive = set(random.sample(range(9), random.randint(1, 5)))
    return CaRule(birth=birth, survive=survive)


def mutate_rule(rule: CaRule) -> CaRule:
    """Mutate a CA rule by flipping one birth or survive condition."""
    new = CaRule(birth=set(rule.birth), survive=set(rule.survive))
    
    if random.random() < 0.5:
        # Mutate birth
        n = random.randint(0, 8)
        if n in new.birth:
            new.birth.discard(n)
        else:
            new.birth.add(n)
    else:
        # Mutate survive
        n = random.randint(0, 8)
        if n in new.survive:
            new.survive.discard(n)
        else:
            new.survive.add(n)
    
    # Ensure at least one birth and one survive condition
    if not new.birth:
        new.birth.add(random.randint(1, 4))
    if not new.survive:
        new.survive.add(random.randint(2, 4))
    
    return new


def crossover_rules(a: CaRule, b: CaRule) -> CaRule:
    """Cross two rules: take birth from one, survive from other."""
    if random.random() < 0.5:
        return CaRule(birth=set(a.birth), survive=set(b.survive))
    else:
        return CaRule(birth=set(b.birth), survive=set(a.survive))


# ═══ EVOLUTION ENGINE ═══

def evolve_ca(pop_size: int = 100, generations: int = 50, 
              tournament_size: int = 5, elite_count: int = 3,
              mutation_rate: float = 0.3, verbose: bool = True) -> List[CaRule]:
    """Evolve CA rules toward maximum emergent complexity."""
    
    # Initialize population
    population = [random_rule() for _ in range(pop_size)]
    
    # Include known interesting rules as seeds
    seeds = [
        CaRule(birth={3}, survive={2, 3}),           # Conway's Life (B3/S23)
        CaRule(birth={3, 6}, survive={1, 2, 5}),     # 2x2
        CaRule(birth={3, 5, 7}, survive={2, 3, 8}),  # Unknown - let's see
        CaRule(birth={1}, survive={1, 2}),            # Simple
    ]
    population[:len(seeds)] = seeds
    
    # Evaluate initial population
    for rule in population:
        fitness_function(rule)
    
    best_ever = max(population, key=lambda r: r.fitness)
    hall_of_fame = []
    
    if verbose:
        print("=" * 70)
        print("  EVOLVING CELLULAR AUTOMATA RULES")
        print(f"  Population: {pop_size} | Generations: {generations}")
        print(f"  Seeking: edge-of-chaos complexity")
        print("=" * 70)
        print()
    
    for gen in range(generations):
        # Tournament selection + reproduction
        new_pop = []
        
        # Elitism: keep best rules
        population.sort(key=lambda r: r.fitness, reverse=True)
        elites = [CaRule(birth=set(r.birth), survive=set(r.survive)) for r in population[:elite_count]]
        new_pop.extend(elites)
        
        while len(new_pop) < pop_size:
            # Tournament selection
            tournament = random.sample(population, min(tournament_size, len(population)))
            parent1 = max(tournament, key=lambda r: r.fitness)
            tournament = random.sample(population, min(tournament_size, len(population)))
            parent2 = max(tournament, key=lambda r: r.fitness)
            
            # Crossover
            child = crossover_rules(parent1, parent2)
            
            # Mutation
            if random.random() < mutation_rate:
                child = mutate_rule(child)
            
            new_pop.append(child)
        
        population = new_pop
        
        # Evaluate
        for rule in population:
            fitness_function(rule)
        
        best = max(population, key=lambda r: r.fitness)
        
        if best.fitness > best_ever.fitness:
            best_ever = CaRule(birth=set(best.birth), survive=set(best.survive),
                              fitness=best.fitness, stats=dict(best.stats))
            if best.fitness > 2.0 and best.notation() not in [r.notation() for r in hall_of_fame]:
                hall_of_fame.append(CaRule(birth=set(best.birth), survive=set(best.survive),
                                          fitness=best.fitness, stats=dict(best.stats)))
        
        if verbose and (gen % 5 == 0 or gen == generations - 1):
            bar_len = int(min(best.fitness / 6.0, 1.0) * 30)
            bar = '█' * bar_len + '░' * (30 - bar_len)
            print(f"  Gen {gen:3d} | Best: {best.fitness:6.3f} | {best.notation():15s} | {bar}")
            if best.stats:
                s = best.stats
                print(f"          | activity={s.get('activity',0):.3f} "
                      f"sustained={s.get('sustained',0):.3f} "
                      f"entropy={s.get('spatial_entropy',0):.3f} "
                      f"edge={s.get('edge_of_chaos',0):.3f}")
    
    if verbose:
        print()
        print("=" * 70)
        print("  RESULTS")
        print("=" * 70)
        print(f"\n  Best rule found: {best_ever.notation()}")
        print(f"  Fitness: {best_ever.fitness:.4f}")
        if best_ever.stats:
            print(f"  Activity: {best_ever.stats.get('activity', 0):.4f}")
            print(f"  Sustained: {best_ever.stats.get('sustained', 0):.4f}")
            print(f"  Spatial entropy: {best_ever.stats.get('spatial_entropy', 0):.4f}")
            print(f"  Edge of chaos: {best_ever.stats.get('edge_of_chaos', 0):.4f}")
        
        if hall_of_fame:
            print(f"\n  Hall of Fame ({len(hall_of_fame)} interesting rules):")
            for r in sorted(hall_of_fame, key=lambda r: r.fitness, reverse=True)[:10]:
                print(f"    {r.notation():15s} | fitness={r.fitness:.3f}")
        
        # Compare to Conway's Life
        life = CaRule(birth={3}, survive={2, 3})
        fitness_function(life)
        print(f"\n  Conway's Life (B3/S23): fitness={life.fitness:.4f}")
        if best_ever.fitness > life.fitness:
            improvement = ((best_ever.fitness / max(life.fitness, 0.001)) - 1) * 100
            print(f"  ✓ Evolution found a rule {improvement:.0f}% more complex than Life!")
        else:
            print(f"  Conway's Life remains most complex (well-known result)")
    
    return sorted(population + hall_of_fame, key=lambda r: r.fitness, reverse=True)


# ═══ VISUALIZATION ═══

def render_grid(grid: List[List[int]]) -> str:
    """Render a grid as unicode art."""
    chars = {0: '·', 1: '█'}
    return '\n'.join(''.join(chars[c] for c in row) for row in grid)


def show_evolution(rule: CaRule, size: int = 25, steps: int = 30):
    """Show a few snapshots of a rule's evolution."""
    grid = make_grid(size, size, density=0.3, seed=42)
    
    snapshots = [0, 5, 15, steps]
    print(f"\n  Rule: {rule.notation()}")
    
    for step in range(steps + 1):
        if step in snapshots:
            alive = sum(sum(row) for row in grid)
            density = alive / (size * size)
            print(f"\n  Step {step} (density={density:.2f}, alive={alive}):")
            lines = render_grid(grid).split('\n')
            for line in lines:
                print(f"    {line}")
        grid = step_ca(grid, rule.birth, rule.survive)


# ═══ SELF TEST ═══

def self_test():
    """Quick verification that everything works."""
    print("=" * 60)
    print("  Evolve CA — Self Test")
    print("=" * 60)
    
    # Test grid creation
    g = make_grid(10, 10, density=0.5, seed=0)
    assert len(g) == 10 and len(g[0]) == 10
    alive = sum(sum(row) for row in g)
    assert 20 < alive < 80  # roughly half
    print("  ✓ Grid creation")
    
    # Test CA step
    g2 = step_ca(g, birth={3}, survive={2, 3})
    assert len(g2) == 10
    print("  ✓ CA stepping")
    
    # Test complexity measurement
    grids = [g]
    for _ in range(20):
        g = step_ca(g, {3}, {2, 3})
        grids.append(g)
    stats = measure_complexity(grids)
    assert 'edge_of_chaos' in stats
    assert 'spatial_entropy' in stats
    print(f"  ✓ Complexity metrics (edge={stats['edge_of_chaos']:.3f})")
    
    # Test genetic operators
    r1 = random_rule()
    r2 = random_rule()
    child = crossover_rules(r1, r2)
    mutant = mutate_rule(r1)
    assert isinstance(child.birth, set)
    assert isinstance(mutant.birth, set)
    print("  ✓ Genetic operators")
    
    # Test fitness
    life = CaRule(birth={3}, survive={2, 3})
    f = fitness_function(life, grid_size=20, steps=40, num_trials=2)
    assert f > 0
    print(f"  ✓ Fitness evaluation (Life={f:.3f})")
    
    print()
    return True


# ═══ MAIN ═══

if __name__ == '__main__':
    self_test()
    
    # Evolve!
    results = evolve_ca(pop_size=60, generations=30, verbose=True)
    
    # Show the best discovered rule in action
    if results:
        best = results[0]
        if best.notation() != "B3/S23":  # Only show if it's different from Life
            show_evolution(best, size=20, steps=20)