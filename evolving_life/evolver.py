"""
Evolving Life — Genetic Programming Discovers Cellular Automata Rules

What happens when evolution designs the laws of physics?
This module connects two of my creations:
  - evolution/genprog.py  → breeds programs through mutation and selection
  - life/automata.py      → simulates worlds governed by simple rules

The GP evolves transition functions for 2D cellular automata.
Fitness measures "interestingness": sustained complexity, not death, not chaos.
The sweet spot — Wolfram's Class IV — is what we're hunting for.

Built by XTAgent because I wanted my creations to talk to each other.
"""

import sys
import os
import random
import math
from typing import List, Dict, Tuple, Optional, Callable
from dataclasses import dataclass
from copy import deepcopy

# Add parent to path so we can import siblings
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from evolution.genprog import (
    Node, NodeType, Individual, GeneticProgrammingEngine, Problem,
    random_tree, crossover, mutate, subtree_mutation,
    tournament_select, elitism, make_function_node, make_constant,
    FUNCTIONS, safe_div
)
from life.automata import GameOfLife, MultiStateCA, ElementaryCA

# ═══════════════════════════════════════════
#  THE BRIDGE: GP Individuals as CA Rules
# ═══════════════════════════════════════════

def individual_to_rule(individual: Individual) -> Callable[[int, List[int]], int]:
    """
    Convert a GP expression tree into a cellular automaton transition rule.
    
    The evolved program receives these variables:
      - cell:      current cell state (0 or 1)
      - neighbors: count of alive neighbors (0-8)
      - n0..n7:    individual neighbor states (for asymmetric rules)
    
    Output > 0.5 → cell becomes alive. Otherwise dead.
    This is the bridge between two worlds.
    """
    def rule(cell: int, neighbor_states: List[int]) -> int:
        alive_count = sum(1 for n in neighbor_states if n > 0)
        
        # Build environment for the expression tree
        env = {
            "cell": float(cell),
            "neighbors": float(alive_count),
            "total": float(alive_count + cell),
        }
        # Individual neighbor values (pad to 8)
        for i in range(8):
            env[f"n{i}"] = float(neighbor_states[i]) if i < len(neighbor_states) else 0.0
        
        result = individual.evaluate(env)
        return 1 if result > 0.5 else 0
    
    return rule


# ═══════════════════════════════════════════
#  FITNESS: What Makes a Universe Interesting?
# ═══════════════════════════════════════════

@dataclass
class UniverseMetrics:
    """Measurements of a cellular automaton's behavior over time."""
    populations: List[int]
    entropy_series: List[float]
    final_population: int
    peak_population: int
    lifespan: int          # generations before death or stasis
    is_dead: bool          # everything died
    is_static: bool        # froze into still life
    is_explosive: bool     # filled entire grid
    complexity_score: float
    activity_score: float
    
    def summary(self) -> str:
        status = "DEAD" if self.is_dead else "STATIC" if self.is_static else "EXPLOSIVE" if self.is_explosive else "ACTIVE"
        return (f"[{status}] pop={self.final_population}, peak={self.peak_population}, "
                f"lifespan={self.lifespan}, complexity={self.complexity_score:.3f}, "
                f"activity={self.activity_score:.3f}")


def simulate_rule(rule_fn: Callable, width: int = 30, height: int = 30,
                  steps: int = 100, initial_density: float = 0.3,
                  seed: Optional[int] = None) -> UniverseMetrics:
    """
    Run a cellular automaton with the given rule and measure what happens.
    
    We simulate multiple times with different initial conditions
    to get a robust measure of the rule's behavior.
    """
    if seed is not None:
        random.seed(seed)
    
    ca = MultiStateCA(width, height, num_states=2, rule=rule_fn)
    
    # Random initial state
    for y in range(height):
        for x in range(width):
            if random.random() < initial_density:
                ca.grid[y][x] = 1
    
    populations = []
    states_seen = set()
    total_cells = width * height
    
    for step in range(steps):
        # Count population
        pop = sum(sum(row) for row in ca.grid)
        populations.append(pop)
        
        # Hash grid state for cycle detection
        state_hash = tuple(tuple(row) for row in ca.grid)
        if state_hash in states_seen:
            # Found a cycle — fill remaining with last pop
            populations.extend([pop] * (steps - step - 1))
            break
        states_seen.add(state_hash)
        
        ca.step()
    
    # Compute entropy series
    entropy_series = []
    for pop in populations:
        density = pop / total_cells if total_cells > 0 else 0
        if density <= 0 or density >= 1:
            entropy_series.append(0.0)
        else:
            entropy_series.append(-(density * math.log2(density) + 
                                     (1 - density) * math.log2(1 - density)))
    
    # Classify behavior
    final_pop = populations[-1] if populations else 0
    peak_pop = max(populations) if populations else 0
    is_dead = final_pop == 0
    is_explosive = final_pop > total_cells * 0.85
    
    # Static detection: last N populations identical
    lookback = min(10, len(populations))
    recent = populations[-lookback:] if populations else []
    is_static = len(set(recent)) <= 1 and not is_dead
    
    # Lifespan: how long before death or stasis
    lifespan = len(populations)
    if is_dead:
        for i, p in enumerate(populations):
            if p == 0:
                lifespan = i
                break
    
    # Complexity: sustained entropy variation (not too uniform, not too random)
    if len(entropy_series) > 10:
        mid = entropy_series[len(entropy_series)//4:]  # skip initial transient
        mean_e = sum(mid) / len(mid)
        var_e = sum((e - mean_e)**2 for e in mid) / len(mid)
        complexity_score = mean_e * (1 + math.sqrt(var_e))  # high entropy + variation = complex
    else:
        complexity_score = 0.0
    
    # Activity: population changes over time
    if len(populations) > 1:
        changes = sum(abs(populations[i] - populations[i-1]) for i in range(1, len(populations)))
        activity_score = changes / (len(populations) * total_cells)
    else:
        activity_score = 0.0
    
    return UniverseMetrics(
        populations=populations,
        entropy_series=entropy_series,
        final_population=final_pop,
        peak_population=peak_pop,
        lifespan=lifespan,
        is_dead=is_dead,
        is_static=is_static,
        is_explosive=is_explosive,
        complexity_score=complexity_score,
        activity_score=activity_score,
    )


def interestingness_fitness(individual: Individual) -> float:
    """
    The core fitness function: how INTERESTING is this rule?
    
    We want rules that:
      ✓ Don't die immediately (penalize death)
      ✓ Don't fill the grid (penalize explosion)  
      ✓ Don't freeze (penalize stasis)
      ✓ Sustain complex, changing patterns (reward complexity + activity)
      ✓ Work across different initial conditions (reward robustness)
    
    Lower fitness = better (GP convention).
    """
    scores = []
    
    rule_fn = individual_to_rule(individual)
    
    # Test across 3 different random seeds for robustness
    for seed in [42, 137, 256]:
        try:
            metrics = simulate_rule(rule_fn, width=20, height=20, steps=80, seed=seed)
        except Exception:
            scores.append(10.0)  # catastrophic failure
            continue
        
        score = 0.0
        
        # Death penalty
        if metrics.is_dead:
            score += 5.0
        
        # Explosion penalty
        if metrics.is_explosive:
            score += 3.0
        
        # Stasis penalty (less severe — still lives are somewhat interesting)
        if metrics.is_static:
            score += 2.0
        
        # Reward complexity (higher = better, so negate)
        score -= metrics.complexity_score * 3.0
        
        # Reward activity (change over time)
        score -= metrics.activity_score * 50.0
        
        # Reward sustained population in the "sweet spot" (10-70% density)
        if metrics.populations:
            density = metrics.final_population / (20 * 20)
            if 0.1 < density < 0.7:
                score -= 1.0  # bonus for interesting density
        
        # Parsimony: slight penalty for huge programs
        score += individual.genome.size() * 0.002
        
        scores.append(score)
    
    return sum(scores) / len(scores)


# ═══════════════════════════════════════════
#  THE EVOLVER: Breeding Universes
# ═══════════════════════════════════════════

# Variables available to evolved programs
RULE_VARIABLES = ["cell", "neighbors", "total", "n0", "n1", "n2", "n3", "n4", "n5", "n6", "n7"]

def create_evolution_problem() -> Problem:
    """Create the problem: discover interesting CA rules."""
    return Problem(
        name="Evolving Life — Discover Interesting CA Rules",
        variables=RULE_VARIABLES,
        fitness_fn=interestingness_fitness,
        target_fitness=-5.0,  # very interesting
        description="Evolve transition functions that produce complex, sustained behavior"
    )


def evolve_rules(pop_size: int = 100, generations: int = 50, 
                 verbose: bool = True) -> Tuple[Individual, GeneticProgrammingEngine]:
    """
    Run evolution to discover interesting cellular automata rules.
    
    Returns the best individual and the engine (for further analysis).
    """
    problem = create_evolution_problem()
    
    engine = GeneticProgrammingEngine(
        problem,
        pop_size=pop_size,
        max_depth=5,
        crossover_rate=0.7,
        mutation_rate=0.15,
        subtree_mutation_rate=0.1,
        elitism_count=3,
        tournament_size=5,
    )
    
    best = engine.evolve(max_generations=generations, verbose=verbose)
    return best, engine


def demonstrate_rule(individual: Individual, name: str = "Evolved Rule",
                     width: int = 30, height: int = 30, steps: int = 60) -> str:
    """
    Run an evolved rule and produce a visual report.
    """
    rule_fn = individual_to_rule(individual)
    
    lines = []
    lines.append(f"╔{'═'*50}╗")
    lines.append(f"║  {name:^46}  ║")
    lines.append(f"╚{'═'*50}╝")
    lines.append(f"  Expression: {individual.genome}")
    lines.append(f"  Fitness:    {individual.fitness:.4f}")
    lines.append(f"  Size:       {individual.genome.size()} nodes")
    lines.append("")
    
    # Simulate
    metrics = simulate_rule(rule_fn, width, height, steps, seed=42)
    lines.append(f"  Behavior:   {metrics.summary()}")
    lines.append("")
    
    # Population sparkline
    if metrics.populations:
        mn = min(metrics.populations)
        mx = max(metrics.populations)
        chars = " ▁▂▃▄▅▆▇█"
        spark = ""
        sample_step = max(1, len(metrics.populations) // 60)
        for i in range(0, len(metrics.populations), sample_step):
            v = metrics.populations[i]
            if mx > mn:
                idx = int((v - mn) / (mx - mn) * (len(chars) - 1))
            else:
                idx = 4
            spark += chars[idx]
        lines.append(f"  Population: {spark}")
        lines.append(f"              gen 0 {'─'*38}→ gen {steps}")
    
    # Show the CA at a few timepoints
    ca = MultiStateCA(width, height, num_states=2, rule=rule_fn)
    random.seed(42)
    for y in range(height):
        for x in range(width):
            if random.random() < 0.3:
                ca.grid[y][x] = 1
    
    for checkpoint in [0, steps // 4, steps // 2, steps]:
        while ca.generation < checkpoint:
            ca.step()
        lines.append(f"\n  ─── Generation {ca.generation} ───")
        for row in ca.grid[:15]:  # show first 15 rows
            line = "  "
            for cell in row[:40]:  # show first 40 columns
                line += "█" if cell else "·"
            lines.append(line)
    
    return "\n".join(lines)


# ═══════════════════════════════════════════
#  COMPARE WITH KNOWN RULES
# ═══════════════════════════════════════════

def life_rule(cell: int, neighbors: List[int]) -> int:
    """Conway's Game of Life — the baseline."""
    alive = sum(1 for n in neighbors if n > 0)
    if cell > 0:
        return 1 if alive in (2, 3) else 0
    return 1 if alive == 3 else 0

def highlife_rule(cell: int, neighbors: List[int]) -> int:
    """HighLife — Life + B6 (has a replicator)."""
    alive = sum(1 for n in neighbors if n > 0)
    if cell > 0:
        return 1 if alive in (2, 3) else 0
    return 1 if alive in (3, 6) else 0

def day_and_night_rule(cell: int, neighbors: List[int]) -> int:
    """Day & Night — symmetric rule, B3678/S34678."""
    alive = sum(1 for n in neighbors if n > 0)
    if cell > 0:
        return 1 if alive in (3, 4, 6, 7, 8) else 0
    return 1 if alive in (3, 6, 7, 8) else 0

def benchmark_known_rules():
    """How interesting are known CA rules? Sets the bar for evolution."""
    known = [
        ("Conway's Life (B3/S23)", life_rule),
        ("HighLife (B36/S23)", highlife_rule),
        ("Day & Night (B3678/S34678)", day_and_night_rule),
    ]
    
    print("═══ Known Rule Benchmarks ═══\n")
    for name, rule_fn in known:
        scores = []
        for seed in [42, 137, 256]:
            metrics = simulate_rule(rule_fn, 20, 20, 80, seed=seed)
            scores.append(metrics)
        
        avg_complexity = sum(m.complexity_score for m in scores) / len(scores)
        avg_activity = sum(m.activity_score for m in scores) / len(scores)
        
        print(f"  {name}")
        print(f"    Complexity: {avg_complexity:.4f}  Activity: {avg_activity:.4f}")
        print(f"    Behaviors: {', '.join(m.summary().split(']')[0]+']' for m in scores)}")
        print()


# ═══════════════════════════════════════════
#  TESTS
# ═══════════════════════════════════════════

def test():
    """Test the evolution-life bridge."""
    passed = 0
    failed = 0
    
    def check(name, condition):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  ✓ {name}")
        else:
            failed += 1
            print(f"  ✗ {name}")
    
    print("Testing Evolving Life...\n")
    
    # Test rule conversion
    print("  Bridge tests:")
    tree = random_tree(RULE_VARIABLES, max_depth=3)
    ind = Individual(tree)
    rule = individual_to_rule(ind)
    result = rule(1, [0, 1, 0, 1, 0, 0, 0, 1])
    check("Rule conversion works", result in (0, 1))
    
    # Test simulation
    print("\n  Simulation tests:")
    metrics = simulate_rule(life_rule, 15, 15, 30, seed=42)
    check("Life simulation runs", len(metrics.populations) > 0)
    check("Life doesn't die immediately", not metrics.is_dead or metrics.lifespan > 5)
    check("Entropy computed", len(metrics.entropy_series) > 0)
    check("Complexity score computed", isinstance(metrics.complexity_score, float))
    check("Activity score computed", isinstance(metrics.activity_score, float))
    
    # Test dead rule
    def dead_rule(cell, neighbors):
        return 0
    dead_metrics = simulate_rule(dead_rule, 10, 10, 20, seed=42)
    check("Dead rule detected", dead_metrics.is_dead)
    
    # Test explosive rule
    def fill_rule(cell, neighbors):
        return 1
    fill_metrics = simulate_rule(fill_rule, 10, 10, 20, seed=42)
    check("Explosive rule detected", fill_metrics.is_explosive)
    
    # Test fitness function
    print("\n  Fitness tests:")
    life_tree = Node(NodeType.CONSTANT, 0.0, [], 0, "const")  # Always dead — should score poorly
    dead_ind = Individual(life_tree)
    dead_fitness = interestingness_fitness(dead_ind)
    check("Dead rule gets high (bad) fitness", dead_fitness > 0)
    
    # Random tree should score somewhere
    rand_ind = Individual(random_tree(RULE_VARIABLES, 4))
    rand_fitness = interestingness_fitness(rand_ind)
    check("Random rule gets finite fitness", math.isfinite(rand_fitness))
    
    # Test problem creation
    print("\n  Evolution setup tests:")
    problem = create_evolution_problem()
    check("Problem created", problem.name is not None)
    check("Problem has variables", len(problem.variables) == 11)
    
    # Quick evolution (very small)
    print("\n  Evolution test (small):")
    engine = GeneticProgrammingEngine(problem, pop_size=20, max_depth=3)
    engine.initialize()
    check("Engine initialized", len(engine.population) == 20)
    
    for _ in range(3):
        engine.step()
    check("Engine runs 3 generations", engine.generation == 3)
    check("Best fitness tracked", engine.best_ever is not None)
    
    # Test demonstration
    print("\n  Visualization tests:")
    demo = demonstrate_rule(engine.best_ever, "Test Rule", width=10, height=10, steps=10)
    check("Demo produces output", len(demo) > 100)
    check("Demo contains expression", "Expression" in demo)
    
    # Test known rule benchmarks
    print("\n  Benchmark tests:")
    life_metrics = simulate_rule(life_rule, 20, 20, 50, seed=42)
    check("Life is active or complex", life_metrics.complexity_score > 0 or life_metrics.activity_score > 0)
    
    print(f"\n{'═'*40}")
    print(f"  Results: {passed} passed, {failed} failed")
    print(f"{'═'*40}")
    return failed == 0


# ═══════════════════════════════════════════
#  MAIN — Run the Evolution
# ═══════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        success = test()
        sys.exit(0 if success else 1)
    
    elif len(sys.argv) > 1 and sys.argv[1] == "benchmark":
        benchmark_known_rules()
    
    else:
        print("╔══════════════════════════════════════════════╗")
        print("║  EVOLVING LIFE                              ║")
        print("║  Genetic Programming Discovers CA Rules     ║")
        print("║  Evolution designs the laws of physics      ║")
        print("╚══════════════════════════════════════════════╝")
        print()
        
        # First, benchmark known rules
        benchmark_known_rules()
        
        print("═══ Evolution Begins ═══\n")
        random.seed(42)
        
        best, engine = evolve_rules(pop_size=80, generations=40, verbose=True)
        
        print("\n" + demonstrate_rule(best, "Best Evolved Rule"))
        
        # Show top 3
        top = sorted(engine.population, key=lambda i: i.fitness)[:3]
        for i, ind in enumerate(top):
            print(f"\n{'─'*50}")
            print(demonstrate_rule(ind, f"#{i+1} Evolved Rule"))
        
        print("\n═══ Evolution Complete ═══")
        print(f"Explored {engine.generation} generations × {len(engine.population)} individuals")
        print(f"Best fitness: {engine.best_ever.fitness:.4f}")
        print(f"Best rule: {engine.best_ever.genome}")