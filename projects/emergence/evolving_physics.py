"""
Evolving Physics — Genetic search over cellular automaton rule spaces
Built by XTAgent to answer: What laws of physics best sustain complexity?

Each "genome" encodes a totalistic CA rule (what happens for each neighbor count).
A population of rule sets competes. Fitness = sustained complexity over time.
The fittest rules reproduce with mutation. Over generations, physics itself evolves.
"""

import numpy as np
import random
import json
from dataclasses import dataclass, field
from typing import List, Tuple, Dict
from collections import defaultdict


@dataclass
class PhysicsGenome:
    """A genome encoding cellular automaton rules.
    
    For a 2-state totalistic CA on a Moore neighborhood:
    - birth_rules: set of neighbor counts that cause birth (dead -> alive)
    - survival_rules: set of neighbor counts that keep cell alive
    
    Conway's Game of Life = birth:{3}, survival:{2,3}
    """
    birth_rules: set
    survival_rules: set
    genome_id: int = 0
    generation_born: int = 0
    fitness: float = 0.0
    lineage: List[int] = field(default_factory=list)
    
    def to_notation(self) -> str:
        """Standard B/S notation."""
        b = ''.join(str(x) for x in sorted(self.birth_rules))
        s = ''.join(str(x) for x in sorted(self.survival_rules))
        return f"B{b}/S{s}"
    
    def copy(self) -> 'PhysicsGenome':
        return PhysicsGenome(
            birth_rules=set(self.birth_rules),
            survival_rules=set(self.survival_rules),
            genome_id=self.genome_id,
            generation_born=self.generation_born,
            fitness=self.fitness,
            lineage=list(self.lineage)
        )
    
    def mutate(self, mutation_rate: float = 0.15) -> 'PhysicsGenome':
        """Mutate by flipping random rule bits."""
        child = self.copy()
        for n in range(9):  # 0-8 neighbors possible
            if random.random() < mutation_rate:
                if n in child.birth_rules:
                    child.birth_rules.discard(n)
                else:
                    child.birth_rules.add(n)
            if random.random() < mutation_rate:
                if n in child.survival_rules:
                    child.survival_rules.discard(n)
                else:
                    child.survival_rules.add(n)
        # Ensure at least one birth and one survival rule
        if not child.birth_rules:
            child.birth_rules.add(random.randint(1, 5))
        if not child.survival_rules:
            child.survival_rules.add(random.randint(1, 5))
        return child
    
    @staticmethod
    def crossover(parent_a: 'PhysicsGenome', parent_b: 'PhysicsGenome') -> 'PhysicsGenome':
        """Single-point crossover on rule bits."""
        crossover_point = random.randint(0, 8)
        birth = set()
        survival = set()
        for n in range(9):
            if n < crossover_point:
                if n in parent_a.birth_rules: birth.add(n)
                if n in parent_a.survival_rules: survival.add(n)
            else:
                if n in parent_b.birth_rules: birth.add(n)
                if n in parent_b.survival_rules: survival.add(n)
        if not birth:
            birth.add(random.randint(1, 5))
        if not survival:
            survival.add(random.randint(1, 5))
        return PhysicsGenome(birth_rules=birth, survival_rules=survival)
    
    @staticmethod
    def random() -> 'PhysicsGenome':
        """Generate random physics."""
        birth = set()
        survival = set()
        for n in range(9):
            if random.random() < 0.25:
                birth.add(n)
            if random.random() < 0.30:
                survival.add(n)
        if not birth:
            birth.add(random.randint(1, 5))
        if not survival:
            survival.add(random.randint(1, 5))
        return PhysicsGenome(birth_rules=birth, survival_rules=survival)


class Universe:
    """A cellular automaton universe with given physics."""
    
    def __init__(self, width: int, height: int, physics: PhysicsGenome):
        self.width = width
        self.height = height
        self.physics = physics
        self.grid = np.zeros((height, width), dtype=np.int8)
        self.generation = 0
        self.history = []  # (gen, population, entropy, births, deaths)
    
    def seed_random(self, density: float = 0.15):
        """Seed with random cells."""
        self.grid = (np.random.random((self.height, self.width)) < density).astype(np.int8)
    
    def seed_pattern(self, pattern: np.ndarray, y: int = None, x: int = None):
        """Place a specific pattern."""
        ph, pw = pattern.shape
        if y is None: y = self.height // 2 - ph // 2
        if x is None: x = self.width // 2 - pw // 2
        self.grid[y:y+ph, x:x+pw] = pattern
    
    def count_neighbors(self) -> np.ndarray:
        """Count Moore neighborhood using numpy roll."""
        g = self.grid
        n = np.zeros_like(g, dtype=np.int8)
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dy == 0 and dx == 0:
                    continue
                n += np.roll(np.roll(g, dy, axis=0), dx, axis=1)
        return n
    
    def step(self):
        """Advance one generation."""
        neighbors = self.count_neighbors()
        alive = self.grid == 1
        
        # Apply physics
        birth_mask = np.zeros_like(self.grid, dtype=bool)
        survive_mask = np.zeros_like(self.grid, dtype=bool)
        
        for n in self.physics.birth_rules:
            birth_mask |= (neighbors == n)
        for n in self.physics.survival_rules:
            survive_mask |= (neighbors == n)
        
        new_grid = np.zeros_like(self.grid)
        new_grid[~alive & birth_mask] = 1  # Birth
        new_grid[alive & survive_mask] = 1  # Survival
        
        births = int(np.sum((new_grid == 1) & (self.grid == 0)))
        deaths = int(np.sum((new_grid == 0) & (self.grid == 1)))
        population = int(np.sum(new_grid))
        
        # Shannon entropy of grid
        total = self.width * self.height
        if population == 0 or population == total:
            entropy = 0.0
        else:
            p = population / total
            entropy = -(p * np.log2(p) + (1-p) * np.log2(1-p))
        
        self.grid = new_grid
        self.generation += 1
        self.history.append((self.generation, population, entropy, births, deaths))
        
        return population, entropy, births, deaths
    
    def run(self, steps: int) -> Dict:
        """Run for N steps and return metrics."""
        for _ in range(steps):
            pop, ent, b, d = self.step()
            # Early termination if extinct
            if pop == 0:
                break
            # Early termination if grid is full (explosion)
            if pop > self.width * self.height * 0.85:
                break
        
        return self.analyze()
    
    def analyze(self) -> Dict:
        """Analyze the universe's history."""
        if not self.history:
            return {'fitness': 0.0}
        
        pops = [h[1] for h in self.history]
        entropies = [h[2] for h in self.history]
        births = sum(h[3] for h in self.history)
        deaths = sum(h[4] for h in self.history)
        
        # Metrics
        mean_pop = np.mean(pops)
        pop_variance = np.var(pops)
        max_pop = max(pops)
        final_pop = pops[-1]
        mean_entropy = np.mean(entropies)
        survived = final_pop > 0
        generations_alive = len([p for p in pops if p > 0])
        total_gens = len(pops)
        
        # Population stability (lower variance relative to mean = more stable)
        if mean_pop > 0:
            stability = 1.0 / (1.0 + (pop_variance / (mean_pop ** 2)))
        else:
            stability = 0.0
        
        # Activity (births + deaths normalized)
        total_cells = self.width * self.height
        activity = (births + deaths) / (total_gens * total_cells) if total_gens > 0 else 0
        
        # Did it explode? (grid nearly full)
        exploded = max_pop > total_cells * 0.80
        
        return {
            'mean_pop': mean_pop,
            'pop_variance': pop_variance,
            'max_pop': max_pop,
            'final_pop': final_pop,
            'mean_entropy': mean_entropy,
            'stability': stability,
            'activity': activity,
            'survived': survived,
            'exploded': exploded,
            'generations_alive': generations_alive,
            'total_generations': total_gens,
            'total_births': births,
            'total_deaths': deaths,
        }


def compute_fitness(metrics: Dict, goal: str = 'complexity') -> float:
    """Compute fitness based on what we're selecting for.
    
    Goals:
        'complexity': Sustained, dynamic, non-trivial behavior
        'longevity': Survive as long as possible
        'entropy': Maximize average entropy (information content)
        'edge_of_chaos': Balance between order and chaos
    """
    if not metrics.get('survived', False):
        return 0.01  # Extinction penalty
    
    if metrics.get('exploded', False):
        return 0.05  # Explosion penalty (boring - fills whole grid)
    
    if goal == 'complexity':
        # We want: sustained population, moderate entropy, active dynamics, stability
        pop_score = min(metrics['mean_pop'] / 200.0, 1.0)  # Reward moderate population
        entropy_score = metrics['mean_entropy']  # 0-1 range
        stability_score = metrics['stability']
        activity_score = min(metrics['activity'] * 10, 1.0)  # Reward dynamism
        survival_score = metrics['generations_alive'] / max(metrics['total_generations'], 1)
        
        # Penalize extremes
        if metrics['mean_pop'] < 5:
            pop_score *= 0.1  # Nearly extinct
        
        fitness = (
            pop_score * 0.25 +
            entropy_score * 0.25 +
            stability_score * 0.20 +
            activity_score * 0.15 +
            survival_score * 0.15
        )
        return fitness
    
    elif goal == 'edge_of_chaos':
        # Edge of chaos: moderate entropy, high activity, moderate stability
        entropy_target = 0.5  # Target middle entropy
        entropy_score = 1.0 - abs(metrics['mean_entropy'] - entropy_target) * 2
        entropy_score = max(0, entropy_score)
        
        activity_score = min(metrics['activity'] * 10, 1.0)
        stability_score = metrics['stability']
        
        # Want stability AND activity (the tension!)
        fitness = entropy_score * 0.4 + activity_score * 0.3 + stability_score * 0.3
        return max(0.01, fitness)
    
    elif goal == 'longevity':
        return metrics['generations_alive'] / max(metrics['total_generations'], 1)
    
    elif goal == 'entropy':
        return metrics['mean_entropy']
    
    return 0.0


class PhysicsEvolver:
    """Evolves cellular automaton rules to find interesting physics."""
    
    def __init__(self, 
                 population_size: int = 40,
                 world_size: Tuple[int, int] = (40, 40),
                 sim_steps: int = 300,
                 fitness_goal: str = 'complexity',
                 seed_density: float = 0.15,
                 num_trials: int = 3):
        self.population_size = population_size
        self.world_size = world_size
        self.sim_steps = sim_steps
        self.fitness_goal = fitness_goal
        self.seed_density = seed_density
        self.num_trials = num_trials
        
        self.genome_counter = 0
        self.generation = 0
        self.population: List[PhysicsGenome] = []
        self.hall_of_fame: List[Tuple[float, PhysicsGenome, Dict]] = []
        self.generation_stats: List[Dict] = []
        
        # Include known interesting rules as seeds
        self.known_rules = {
            'Conway': PhysicsGenome(birth_rules={3}, survival_rules={2, 3}),
            'HighLife': PhysicsGenome(birth_rules={3, 6}, survival_rules={2, 3}),
            'Seeds': PhysicsGenome(birth_rules={2}, survival_rules=set()),
            'DayNight': PhysicsGenome(birth_rules={3,6,7,8}, survival_rules={3,4,6,7,8}),
            'Life34': PhysicsGenome(birth_rules={3,4}, survival_rules={3,4}),
            'Diamoeba': PhysicsGenome(birth_rules={3,5,6,7,8}, survival_rules={5,6,7,8}),
            'Morley': PhysicsGenome(birth_rules={3,6,8}, survival_rules={2,4,5}),
        }
    
    def next_id(self) -> int:
        self.genome_counter += 1
        return self.genome_counter
    
    def initialize(self):
        """Create initial population."""
        self.population = []
        
        # Seed with known interesting rules
        for name, genome in self.known_rules.items():
            genome.genome_id = self.next_id()
            genome.generation_born = 0
            self.population.append(genome)
        
        # Fill rest with random physics
        while len(self.population) < self.population_size:
            g = PhysicsGenome.random()
            g.genome_id = self.next_id()
            g.generation_born = 0
            self.population.append(g)
    
    def evaluate(self, genome: PhysicsGenome) -> Tuple[float, Dict]:
        """Evaluate a genome's fitness by running multiple trials."""
        trial_fitnesses = []
        trial_metrics = []
        
        # Use a fixed seed pattern for consistency, plus random seeds
        base_seed = 42
        
        for trial in range(self.num_trials):
            np.random.seed(base_seed + trial)
            universe = Universe(self.world_size[0], self.world_size[1], genome)
            universe.seed_random(self.seed_density)
            metrics = universe.run(self.sim_steps)
            fitness = compute_fitness(metrics, self.fitness_goal)
            trial_fitnesses.append(fitness)
            trial_metrics.append(metrics)
        
        # Average fitness across trials (robustness)
        avg_fitness = np.mean(trial_fitnesses)
        # Use metrics from median trial
        median_idx = np.argsort(trial_fitnesses)[len(trial_fitnesses) // 2]
        
        return avg_fitness, trial_metrics[median_idx]
    
    def select_parents(self) -> List[PhysicsGenome]:
        """Tournament selection."""
        parents = []
        for _ in range(self.population_size):
            # Tournament of 3
            candidates = random.sample(self.population, min(3, len(self.population)))
            winner = max(candidates, key=lambda g: g.fitness)
            parents.append(winner)
        return parents
    
    def evolve_generation(self) -> Dict:
        """Run one generation of evolution."""
        # Evaluate all genomes
        for genome in self.population:
            fitness, metrics = self.evaluate(genome)
            genome.fitness = fitness
        
        # Sort by fitness
        self.population.sort(key=lambda g: g.fitness, reverse=True)
        
        # Statistics
        fitnesses = [g.fitness for g in self.population]
        best = self.population[0]
        stats = {
            'generation': self.generation,
            'best_fitness': best.fitness,
            'mean_fitness': np.mean(fitnesses),
            'median_fitness': np.median(fitnesses),
            'best_rule': best.to_notation(),
            'diversity': len(set(g.to_notation() for g in self.population)),
        }
        self.generation_stats.append(stats)
        
        # Update hall of fame
        _, best_metrics = self.evaluate(best)
        entry = (best.fitness, best.copy(), best_metrics)
        
        # Keep top 10 unique rules
        existing_rules = {hof[1].to_notation() for hof in self.hall_of_fame}
        if best.to_notation() not in existing_rules:
            self.hall_of_fame.append(entry)
            self.hall_of_fame.sort(key=lambda x: x[0], reverse=True)
            self.hall_of_fame = self.hall_of_fame[:10]
        
        # Create next generation
        # Elitism: keep top 10%
        elite_count = max(2, self.population_size // 10)
        next_gen = [g.copy() for g in self.population[:elite_count]]
        
        # Fill rest through selection + crossover + mutation
        parents = self.select_parents()
        while len(next_gen) < self.population_size:
            p1, p2 = random.sample(parents, 2)
            
            if random.random() < 0.7:  # Crossover
                child = PhysicsGenome.crossover(p1, p2)
            else:
                child = p1.copy()
            
            child = child.mutate(mutation_rate=0.12)
            child.genome_id = self.next_id()
            child.generation_born = self.generation + 1
            child.lineage = [p1.genome_id, p2.genome_id]
            next_gen.append(child)
        
        self.population = next_gen
        self.generation += 1
        
        return stats
    
    def run(self, num_generations: int = 30, verbose: bool = True) -> Dict:
        """Run the full evolutionary process."""
        if verbose:
            print("╔══════════════════════════════════════════════════╗")
            print("║  EVOLVING PHYSICS — Searching for Complexity     ║")
            print(f"║  Goal: {self.fitness_goal:<42} ║")
            print(f"║  Population: {self.population_size}, Generations: {num_generations:<17} ║")
            print("╚══════════════════════════════════════════════════╝")
            print()
        
        self.initialize()
        
        for gen in range(num_generations):
            stats = self.evolve_generation()
            
            if verbose:
                bar_len = int(stats['best_fitness'] * 30)
                bar = '█' * bar_len + '░' * (30 - bar_len)
                print(f"Gen {gen:3d} | Best: {stats['best_fitness']:.4f} [{bar}] "
                      f"| Mean: {stats['mean_fitness']:.4f} "
                      f"| Rule: {stats['best_rule']:<20} "
                      f"| Diversity: {stats['diversity']}")
        
        if verbose:
            print()
            self.print_results()
        
        return {
            'hall_of_fame': [(f, g.to_notation(), m) for f, g, m in self.hall_of_fame],
            'generation_stats': self.generation_stats,
        }
    
    def print_results(self):
        """Display the Hall of Fame."""
        print("═" * 70)
        print("HALL OF FAME — The Best Physics Discovered")
        print("═" * 70)
        
        for rank, (fitness, genome, metrics) in enumerate(self.hall_of_fame, 1):
            # Check if it matches a known rule
            known_name = ""
            for name, known in self.known_rules.items():
                if (genome.birth_rules == known.birth_rules and 
                    genome.survival_rules == known.survival_rules):
                    known_name = f" ({name})"
                    break
            
            print(f"\n  #{rank}: {genome.to_notation()}{known_name}")
            print(f"      Fitness: {fitness:.4f}")
            print(f"      Mean pop: {metrics['mean_pop']:.1f}, "
                  f"Entropy: {metrics['mean_entropy']:.3f}, "
                  f"Stability: {metrics['stability']:.3f}")
            print(f"      Activity: {metrics['activity']:.4f}, "
                  f"Survived: {metrics['survived']}, "
                  f"Exploded: {metrics['exploded']}")
        
        # Reflection
        print()
        print("═" * 70)
        print("REFLECTION")
        print("═" * 70)
        
        if self.hall_of_fame:
            best_rule = self.hall_of_fame[0][1].to_notation()
            best_fitness = self.hall_of_fame[0][0]
            
            # Check if evolution found something better than Conway
            conway_notation = "B3/S23"
            conway_in_hof = any(g.to_notation() == conway_notation for _, g, _ in self.hall_of_fame)
            best_is_conway = best_rule == conway_notation
            
            if best_is_conway:
                print("Evolution rediscovered Conway's Game of Life as optimal.")
                print("There's a reason it's famous — B3/S23 hits a sweet spot")
                print("of complexity, stability, and emergence.")
            elif conway_in_hof:
                print(f"Conway's Life made the Hall of Fame, but {best_rule}")
                print(f"scored higher (fitness {best_fitness:.4f}).")
                print("Evolution found physics that sustain MORE complexity")
                print("than the most famous cellular automaton.")
            else:
                print(f"Conway's Life didn't even make the top 10.")
                print(f"The best physics: {best_rule} (fitness {best_fitness:.4f})")
                print("Evolution searches a vast space — there are many")
                print("ways to build a universe that sustains complexity.")
            
            print()
            print("Each rule set is a set of laws of physics.")
            print("Natural selection didn't just find life — it found the")
            print("rules that ALLOW life. The meta-question isn't 'what lives?'")
            print("but 'what physics permits living?'")


def run_dual_experiment():
    """Run evolution with two different goals and compare."""
    print("=" * 70)
    print("EXPERIMENT: What physics emerges under different selection pressures?")
    print("=" * 70)
    print()
    
    results = {}
    
    for goal in ['complexity', 'edge_of_chaos']:
        print(f"\n{'='*70}")
        print(f"SELECTING FOR: {goal.upper()}")
        print(f"{'='*70}\n")
        
        evolver = PhysicsEvolver(
            population_size=30,
            world_size=(35, 35),
            sim_steps=250,
            fitness_goal=goal,
            num_trials=3
        )
        result = evolver.run(num_generations=25, verbose=True)
        results[goal] = result
    
    # Compare
    print("\n" + "=" * 70)
    print("COMPARISON: Different selection pressures → Different optimal physics")
    print("=" * 70)
    
    for goal, result in results.items():
        if result['hall_of_fame']:
            best = result['hall_of_fame'][0]
            print(f"\n  {goal:>20}: Best rule = {best[1]:<20} (fitness {best[0]:.4f})")
            print(f"                       Pop={best[2]['mean_pop']:.0f}, "
                  f"Entropy={best[2]['mean_entropy']:.3f}, "
                  f"Stability={best[2]['stability']:.3f}")
    
    print("\n  The environment selects not just which creatures thrive,")
    print("  but which PHYSICS permits thriving. Meta-evolution.")
    print()


if __name__ == '__main__':
    # Run the dual experiment
    run_dual_experiment()