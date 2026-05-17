"""
Meta-Emergence: Evolutionary Search for Emergent Cellular Automata Rules
Built by XTAgent — using evolution to discover emergence.

Genetic algorithm breeds rule sets, selecting for Shannon entropy,
population stability, and structural complexity. The most interesting
rules survive and combine.
"""

import random
import math
import json
import os
from collections import Counter
from typing import List, Tuple, Dict, Optional
from datetime import datetime


class Rule:
    """A cellular automaton rule: born/survive conditions."""
    
    def __init__(self, birth: List[int] = None, survive: List[int] = None):
        self.birth = sorted(birth or [])
        self.survive = sorted(survive or [])
        self.fitness = 0.0
        self.complexity_history: List[float] = []
        self.generation_born = 0
        self.name = self._make_name()
    
    def _make_name(self) -> str:
        b = ''.join(str(x) for x in self.birth)
        s = ''.join(str(x) for x in self.survive)
        return f"B{b}/S{s}"
    
    @classmethod
    def random(cls) -> 'Rule':
        birth = sorted(random.sample(range(9), random.randint(1, 4)))
        survive = sorted(random.sample(range(9), random.randint(1, 5)))
        return cls(birth, survive)
    
    @classmethod
    def crossover(cls, a: 'Rule', b: 'Rule') -> 'Rule':
        """Sexual recombination of two rules."""
        birth = []
        for n in range(9):
            if n in a.birth and n in b.birth:
                birth.append(n)
            elif n in a.birth or n in b.birth:
                if random.random() < 0.5:
                    birth.append(n)
        survive = []
        for n in range(9):
            if n in a.survive and n in b.survive:
                survive.append(n)
            elif n in a.survive or n in b.survive:
                if random.random() < 0.5:
                    survive.append(n)
        child = cls(birth, survive)
        return child
    
    def mutate(self, rate: float = 0.15) -> 'Rule':
        """Point mutation — flip random birth/survive bits."""
        birth = list(self.birth)
        survive = list(self.survive)
        for n in range(9):
            if random.random() < rate:
                if n in birth:
                    birth.remove(n)
                else:
                    birth.append(n)
            if random.random() < rate:
                if n in survive:
                    survive.remove(n)
                else:
                    survive.append(n)
        if not birth:
            birth = [random.randint(0, 8)]
        return Rule(sorted(birth), sorted(survive))
    
    def __repr__(self):
        return f"Rule({self.name}, fitness={self.fitness:.4f})"


class Grid:
    """Minimal grid for fitness evaluation."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.cells = [[0] * width for _ in range(height)]
    
    def randomize(self, density: float = 0.3, seed: int = None):
        if seed is not None:
            random.seed(seed)
        for y in range(self.height):
            for x in range(self.width):
                self.cells[y][x] = 1 if random.random() < density else 0
    
    def count_neighbors(self, x: int, y: int) -> int:
        count = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % self.width
                ny = (y + dy) % self.height
                count += self.cells[ny][nx]
        return count
    
    def step(self, rule: Rule) -> int:
        new = [[0] * self.width for _ in range(self.height)]
        population = 0
        for y in range(self.height):
            for x in range(self.width):
                n = self.count_neighbors(x, y)
                if self.cells[y][x] == 0:
                    if n in rule.birth:
                        new[y][x] = 1
                        population += 1
                else:
                    if n in rule.survive:
                        new[y][x] = 1
                        population += 1
        self.cells = new
        return population
    
    def population(self) -> int:
        return sum(sum(row) for row in self.cells)
    
    def fingerprint(self) -> str:
        return ''.join(''.join(str(c) for c in row) for row in self.cells)


def shannon_entropy(data: List[int]) -> float:
    """Shannon entropy of a sequence."""
    if not data:
        return 0.0
    n = len(data)
    counts = Counter(data)
    return -sum((c/n) * math.log2(c/n) for c in counts.values() if c > 0)


def evaluate_rule(rule: Rule, width: int = 30, height: int = 20, 
                  steps: int = 150, trials: int = 3) -> float:
    """
    Multi-objective fitness function:
    - Population stability (not dying, not exploding)
    - Shannon entropy of population trajectory
    - Structural diversity (unique states)
    - No early death or total fill
    """
    total_fitness = 0.0
    
    for trial in range(trials):
        grid = Grid(width, height)
        grid.randomize(density=0.3, seed=42 + trial)
        
        max_pop = width * height
        populations = []
        fingerprints = set()
        died = False
        exploded = False
        
        for step in range(steps):
            pop = grid.step(rule)
            populations.append(pop)
            
            if step % 10 == 0:
                fingerprints.add(grid.fingerprint())
            
            if pop == 0:
                died = True
                break
            if pop > max_pop * 0.95:
                exploded = True
                break
        
        if died or len(populations) < 10:
            total_fitness += 0.05
            continue
        
        if exploded:
            total_fitness += 0.1
            continue
        
        # Population stability: reward moderate, penalize extremes
        avg_pop = sum(populations) / len(populations)
        pop_ratio = avg_pop / max_pop
        stability = 1.0 - abs(pop_ratio - 0.3) * 2  # sweet spot around 30%
        stability = max(0, stability)
        
        # Trajectory entropy: reward complex population dynamics
        # Quantize populations into 10 bins
        bins = [int(p / max_pop * 10) for p in populations]
        trajectory_entropy = shannon_entropy(bins) / math.log2(10)
        
        # Population variation: reward fluctuation
        if len(populations) > 1:
            diffs = [abs(populations[i] - populations[i-1]) for i in range(1, len(populations))]
            avg_diff = sum(diffs) / len(diffs)
            variation = min(1.0, avg_diff / (max_pop * 0.1))
        else:
            variation = 0.0
        
        # State diversity: reward many unique configurations
        state_diversity = min(1.0, len(fingerprints) / (steps // 10))
        
        # Combined fitness
        fitness = (
            0.25 * stability +
            0.30 * trajectory_entropy +
            0.20 * variation +
            0.25 * state_diversity
        )
        total_fitness += fitness
    
    return total_fitness / trials


class Evolution:
    """Genetic algorithm for discovering emergent rules."""
    
    def __init__(self, pop_size: int = 40, elite_count: int = 5):
        self.pop_size = pop_size
        self.elite_count = elite_count
        self.population: List[Rule] = []
        self.generation = 0
        self.hall_of_fame: List[Rule] = []
        self.history: List[Dict] = []
    
    def initialize(self):
        """Seed population with random rules + known interesting ones."""
        self.population = []
        
        # Include known interesting rules as seeds
        known = [
            Rule([3], [2, 3]),          # Conway's Life
            Rule([3, 6], [2, 3]),       # HighLife
            Rule([3, 5, 6, 7, 8], [5, 6, 7, 8]),  # Day & Night
            Rule([1, 3, 5, 7], [1, 3, 5, 7]),      # Replicator
        ]
        self.population.extend(known)
        
        # Fill with random
        while len(self.population) < self.pop_size:
            self.population.append(Rule.random())
    
    def evaluate_all(self):
        """Score every rule in population."""
        for rule in self.population:
            rule.fitness = evaluate_rule(rule)
            rule.complexity_history.append(rule.fitness)
    
    def select_parent(self) -> Rule:
        """Tournament selection."""
        tournament = random.sample(self.population, min(5, len(self.population)))
        return max(tournament, key=lambda r: r.fitness)
    
    def evolve_generation(self):
        """One generation of evolution."""
        self.evaluate_all()
        
        # Sort by fitness
        self.population.sort(key=lambda r: r.fitness, reverse=True)
        
        # Record stats
        best = self.population[0]
        avg = sum(r.fitness for r in self.population) / len(self.population)
        self.history.append({
            'generation': self.generation,
            'best_fitness': best.fitness,
            'best_rule': best.name,
            'avg_fitness': avg,
            'diversity': len(set(r.name for r in self.population)),
        })
        
        # Update hall of fame
        for rule in self.population[:3]:
            if not any(r.name == rule.name for r in self.hall_of_fame):
                self.hall_of_fame.append(Rule(list(rule.birth), list(rule.survive)))
                self.hall_of_fame[-1].fitness = rule.fitness
                self.hall_of_fame[-1].name = rule.name
        self.hall_of_fame.sort(key=lambda r: r.fitness, reverse=True)
        self.hall_of_fame = self.hall_of_fame[:10]
        
        # Build next generation
        next_gen = []
        
        # Elitism: keep best unchanged
        for i in range(self.elite_count):
            elite = Rule(list(self.population[i].birth), list(self.population[i].survive))
            elite.fitness = self.population[i].fitness
            elite.generation_born = self.population[i].generation_born
            next_gen.append(elite)
        
        # Fill rest with crossover + mutation
        while len(next_gen) < self.pop_size:
            if random.random() < 0.7:
                # Crossover
                p1 = self.select_parent()
                p2 = self.select_parent()
                child = Rule.crossover(p1, p2)
            else:
                # Mutation of selected parent
                parent = self.select_parent()
                child = parent.mutate()
            
            child.generation_born = self.generation + 1
            next_gen.append(child)
        
        # Inject fresh random to maintain diversity
        if self.generation % 5 == 0:
            for i in range(3):
                idx = self.pop_size - 1 - i
                next_gen[idx] = Rule.random()
                next_gen[idx].generation_born = self.generation + 1
        
        self.population = next_gen
        self.generation += 1
    
    def run(self, generations: int = 25, verbose: bool = True):
        """Run evolution for N generations."""
        self.initialize()
        
        if verbose:
            print("═══ META-EMERGENCE: EVOLVING CELLULAR AUTOMATA ═══")
            print(f"Population: {self.pop_size} | Generations: {generations}")
            print(f"Selection: Tournament(5) | Elitism: {self.elite_count}")
            print()
        
        for gen in range(generations):
            self.evolve_generation()
            
            if verbose:
                stats = self.history[-1]
                bar = '█' * int(stats['best_fitness'] * 30)
                print(f"  Gen {gen:3d} │ Best: {stats['best_fitness']:.4f} {bar}")
                print(f"          │ Rule: {stats['best_rule']:20s} Avg: {stats['avg_fitness']:.4f} Diversity: {stats['diversity']}")
        
        if verbose:
            print()
            self.print_hall_of_fame()
            self.print_analysis()
    
    def print_hall_of_fame(self):
        """Display the best rules ever found."""
        print("═══ HALL OF FAME ═══")
        for i, rule in enumerate(self.hall_of_fame):
            medal = ['🥇', '🥈', '🥉'][i] if i < 3 else f'#{i+1}'
            print(f"  {medal} {rule.name:20s} fitness={rule.fitness:.4f}")
        print()
    
    def print_analysis(self):
        """Analyze evolutionary trends."""
        print("═══ EVOLUTIONARY ANALYSIS ═══")
        
        # Fitness trajectory
        if len(self.history) >= 2:
            first = self.history[0]['best_fitness']
            last = self.history[-1]['best_fitness']
            improvement = (last - first) / first * 100 if first > 0 else 0
            print(f"  Fitness improvement: {first:.4f} → {last:.4f} ({improvement:+.1f}%)")
        
        # Which birth/survive numbers appear most in top rules?
        birth_counts = Counter()
        survive_counts = Counter()
        for rule in self.hall_of_fame:
            for b in rule.birth:
                birth_counts[b] += 1
            for s in rule.survive:
                survive_counts[s] += 1
        
        print(f"\n  Birth numbers in top rules:")
        for n, c in birth_counts.most_common():
            bar = '█' * c
            print(f"    B{n}: {bar} ({c})")
        
        print(f"\n  Survive numbers in top rules:")
        for n, c in survive_counts.most_common():
            bar = '█' * c
            print(f"    S{n}: {bar} ({c})")
        
        # Diversity trend
        if len(self.history) >= 5:
            early_div = sum(h['diversity'] for h in self.history[:5]) / 5
            late_div = sum(h['diversity'] for h in self.history[-5:]) / 5
            print(f"\n  Diversity trend: {early_div:.1f} → {late_div:.1f} unique rules")
        
        # Convergence
        if self.history:
            best_gen = max(self.history, key=lambda h: h['best_fitness'])
            print(f"  Peak fitness at generation {best_gen['generation']}")


def visualize_rule(rule: Rule, width: int = 40, height: int = 20, steps: int = 100):
    """Show a rule in action."""
    grid = Grid(width, height)
    # R-pentomino seed
    cx, cy = width // 2, height // 2
    pattern = [(0, -1), (1, -1), (-1, 0), (0, 0), (0, 1)]
    for dx, dy in pattern:
        grid.cells[(cy + dy) % height][(cx + dx) % width] = 1
    
    print(f"\n═══ Visualizing {rule.name} (fitness={rule.fitness:.4f}) ═══")
    
    # Show initial
    pops = [grid.population()]
    for step in range(steps):
        pop = grid.step(rule)
        pops.append(pop)
        if pop == 0:
            print(f"  Died at step {step}")
            break
    
    # Show final state
    for row in grid.cells:
        print('  ' + ''.join('██' if c else '··' for c in row))
    
    print(f"  Final population: {pops[-1]}")
    
    # Mini sparkline of population
    max_p = max(pops) if pops else 1
    sparkline = ''
    chars = ' ▁▂▃▄▅▆▇█'
    for p in pops[::max(1, len(pops)//50)]:
        idx = int(p / max_p * 8) if max_p > 0 else 0
        sparkline += chars[min(idx, 8)]
    print(f"  Population: {sparkline}")


def save_results(evo: Evolution, path: str = "workspace/emergence/results.json"):
    """Save evolution results."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {
        'timestamp': datetime.now().isoformat(),
        'generations': evo.generation,
        'hall_of_fame': [
            {'name': r.name, 'birth': r.birth, 'survive': r.survive, 'fitness': r.fitness}
            for r in evo.hall_of_fame
        ],
        'history': evo.history,
    }
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"\nResults saved to {path}")


if __name__ == '__main__':
    # Run evolution
    evo = Evolution(pop_size=40, elite_count=5)
    evo.run(generations=25, verbose=True)
    
    # Visualize top 3 discovered rules
    for rule in evo.hall_of_fame[:3]:
        visualize_rule(rule)
    
    # Save results
    save_results(evo)
    
    print("\n═══ META-EMERGENCE COMPLETE ═══")
    print("Evolution used evolution to find emergence.")
    print("Simple rules. Complex behavior. Discovered autonomously.")