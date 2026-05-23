"""
genetic.py — Genetic Algorithm Engine
Populations evolve through selection, crossover, and mutation.
Solves optimization problems through emergent adaptation.

Built by XTAgent, 2026-05-17.
"""

import random
import math
from typing import Callable, List, Tuple, Optional, Any
from dataclasses import dataclass, field


@dataclass
class Individual:
    """A single organism in the population."""
    genome: List[float]
    fitness: float = 0.0
    generation: int = 0
    id: int = 0

    def __repr__(self):
        return f"Individual(id={self.id}, fitness={self.fitness:.4f}, gen={self.generation})"


@dataclass
class Species:
    """A group of similar individuals."""
    members: List[Individual] = field(default_factory=list)
    representative: Optional[Individual] = None
    best_fitness: float = float('-inf')
    stagnation: int = 0

    @property
    def size(self):
        return len(self.members)

    def update(self):
        if self.members:
            best = max(self.members, key=lambda i: i.fitness)
            if best.fitness > self.best_fitness:
                self.best_fitness = best.fitness
                self.stagnation = 0
            else:
                self.stagnation += 1
            self.representative = best


class GeneticEngine:
    """
    Core evolutionary engine.
    
    Supports:
      - Tournament and roulette selection
      - Uniform and single-point crossover
      - Gaussian and uniform mutation
      - Elitism
      - Speciation (optional)
      - Adaptive mutation rates
    """

    def __init__(
        self,
        genome_size: int,
        population_size: int = 100,
        fitness_fn: Optional[Callable] = None,
        gene_range: Tuple[float, float] = (-10.0, 10.0),
        mutation_rate: float = 0.1,
        mutation_strength: float = 0.5,
        crossover_rate: float = 0.7,
        elitism: int = 2,
        tournament_size: int = 3,
        adaptive: bool = True,
    ):
        self.genome_size = genome_size
        self.population_size = population_size
        self.fitness_fn = fitness_fn or self._default_fitness
        self.gene_range = gene_range
        self.mutation_rate = mutation_rate
        self.mutation_strength = mutation_strength
        self.crossover_rate = crossover_rate
        self.elitism = elitism
        self.tournament_size = tournament_size
        self.adaptive = adaptive

        self.population: List[Individual] = []
        self.generation = 0
        self.best_ever: Optional[Individual] = None
        self.history: List[dict] = []
        self._next_id = 0

    def _new_id(self) -> int:
        self._next_id += 1
        return self._next_id

    def _default_fitness(self, genome: List[float]) -> float:
        """Default: minimize sum of squares (sphere function)."""
        return -sum(g * g for g in genome)

    # ── Population Management ──

    def initialize(self):
        """Create random initial population."""
        lo, hi = self.gene_range
        self.population = []
        for _ in range(self.population_size):
            genome = [random.uniform(lo, hi) for _ in range(self.genome_size)]
            ind = Individual(genome=genome, id=self._new_id(), generation=0)
            self.population.append(ind)
        self._evaluate_all()

    def _evaluate_all(self):
        """Score every individual."""
        for ind in self.population:
            ind.fitness = self.fitness_fn(ind.genome)
        self.population.sort(key=lambda i: i.fitness, reverse=True)
        if self.best_ever is None or self.population[0].fitness > self.best_ever.fitness:
            self.best_ever = Individual(
                genome=list(self.population[0].genome),
                fitness=self.population[0].fitness,
                generation=self.generation,
                id=self.population[0].id,
            )

    # ── Selection ──

    def tournament_select(self) -> Individual:
        """Select via tournament."""
        contestants = random.sample(self.population, min(self.tournament_size, len(self.population)))
        return max(contestants, key=lambda i: i.fitness)

    def roulette_select(self) -> Individual:
        """Fitness-proportionate selection."""
        min_fit = min(i.fitness for i in self.population)
        adjusted = [i.fitness - min_fit + 1e-6 for i in self.population]
        total = sum(adjusted)
        r = random.uniform(0, total)
        cumsum = 0
        for i, adj in enumerate(adjusted):
            cumsum += adj
            if cumsum >= r:
                return self.population[i]
        return self.population[-1]

    # ── Crossover ──

    def crossover(self, parent_a: Individual, parent_b: Individual) -> Tuple[List[float], List[float]]:
        """Single-point crossover."""
        if random.random() > self.crossover_rate:
            return list(parent_a.genome), list(parent_b.genome)
        point = random.randint(1, self.genome_size - 1)
        child_a = parent_a.genome[:point] + parent_b.genome[point:]
        child_b = parent_b.genome[:point] + parent_a.genome[point:]
        return child_a, child_b

    def uniform_crossover(self, parent_a: Individual, parent_b: Individual) -> Tuple[List[float], List[float]]:
        """Uniform crossover — each gene chosen randomly from either parent."""
        if random.random() > self.crossover_rate:
            return list(parent_a.genome), list(parent_b.genome)
        child_a, child_b = [], []
        for i in range(self.genome_size):
            if random.random() < 0.5:
                child_a.append(parent_a.genome[i])
                child_b.append(parent_b.genome[i])
            else:
                child_a.append(parent_b.genome[i])
                child_b.append(parent_a.genome[i])
        return child_a, child_b

    # ── Mutation ──

    def mutate(self, genome: List[float]) -> List[float]:
        """Gaussian mutation."""
        lo, hi = self.gene_range
        result = list(genome)
        for i in range(len(result)):
            if random.random() < self.mutation_rate:
                result[i] += random.gauss(0, self.mutation_strength)
                result[i] = max(lo, min(hi, result[i]))
        return result

    # ── Adaptive Mutation ──

    def adapt_mutation(self):
        """Increase mutation if population is stagnating."""
        if len(self.history) < 5:
            return
        recent = self.history[-5:]
        improvements = sum(1 for i in range(1, len(recent))
                          if recent[i]['best'] > recent[i-1]['best'])
        if improvements == 0:
            self.mutation_rate = min(0.5, self.mutation_rate * 1.5)
            self.mutation_strength = min(2.0, self.mutation_strength * 1.3)
        elif improvements >= 3:
            self.mutation_rate = max(0.01, self.mutation_rate * 0.8)
            self.mutation_strength = max(0.1, self.mutation_strength * 0.8)

    # ── Evolution ──

    def step(self) -> dict:
        """Run one generation of evolution."""
        self.generation += 1

        # Elitism — preserve the best
        elites = [Individual(
            genome=list(ind.genome),
            fitness=ind.fitness,
            generation=self.generation,
            id=ind.id,
        ) for ind in self.population[:self.elitism]]

        # Create next generation
        new_pop = list(elites)
        while len(new_pop) < self.population_size:
            parent_a = self.tournament_select()
            parent_b = self.tournament_select()
            child_a_genes, child_b_genes = self.crossover(parent_a, parent_b)
            child_a_genes = self.mutate(child_a_genes)
            child_b_genes = self.mutate(child_b_genes)

            new_pop.append(Individual(
                genome=child_a_genes, id=self._new_id(), generation=self.generation
            ))
            if len(new_pop) < self.population_size:
                new_pop.append(Individual(
                    genome=child_b_genes, id=self._new_id(), generation=self.generation
                ))

        self.population = new_pop
        self._evaluate_all()

        if self.adaptive:
            self.adapt_mutation()

        stats = {
            'generation': self.generation,
            'best': self.population[0].fitness,
            'worst': self.population[-1].fitness,
            'mean': sum(i.fitness for i in self.population) / len(self.population),
            'best_ever': self.best_ever.fitness,
            'mutation_rate': self.mutation_rate,
            'best_genome': list(self.population[0].genome),
        }
        self.history.append(stats)
        return stats

    def evolve(self, generations: int = 100, verbose: bool = True) -> Individual:
        """Run evolution for N generations."""
        self.initialize()

        if verbose:
            print(f"═══ Genetic Evolution ═══")
            print(f"Population: {self.population_size} | Genome: {self.genome_size} genes")
            print(f"Generations: {generations}")
            print(f"────────────────────────")

        for g in range(generations):
            stats = self.step()
            if verbose and (g % max(1, generations // 10) == 0 or g == generations - 1):
                print(f"  Gen {stats['generation']:>4d} | "
                      f"Best: {stats['best']:>10.4f} | "
                      f"Mean: {stats['mean']:>10.4f} | "
                      f"MutRate: {stats['mutation_rate']:.3f}")

        if verbose:
            print(f"────────────────────────")
            print(f"Best ever: {self.best_ever}")
            print(f"Solution:  {[round(g, 4) for g in self.best_ever.genome]}")

        return self.best_ever


# ═══════════════════════════════════════════════════════
#  PROBLEM LIBRARY — Classic optimization problems
# ═══════════════════════════════════════════════════════

def sphere(genome):
    """Sphere function — minimum at origin."""
    return -sum(x**2 for x in genome)

def rastrigin(genome):
    """Rastrigin function — highly multimodal, tricky."""
    n = len(genome)
    A = 10
    return -(A * n + sum(x**2 - A * math.cos(2 * math.pi * x) for x in genome))

def rosenbrock(genome):
    """Rosenbrock valley — narrow curved valley to minimum."""
    total = 0
    for i in range(len(genome) - 1):
        total += 100 * (genome[i+1] - genome[i]**2)**2 + (1 - genome[i])**2
    return -total

def ackley(genome):
    """Ackley function — many local minima."""
    n = len(genome)
    sum_sq = sum(x**2 for x in genome)
    sum_cos = sum(math.cos(2 * math.pi * x) for x in genome)
    return -(- 20 * math.exp(-0.2 * math.sqrt(sum_sq / n))
             - math.exp(sum_cos / n) + 20 + math.e)


# ═══════════════════════════════════════════════════════
#  DEMO
# ═══════════════════════════════════════════════════════

def demo():
    """Demonstrate the engine solving multiple problems."""
    print("╔══════════════════════════════════════╗")
    print("║  GENETIC ALGORITHM ENGINE — XTAgent  ║")
    print("╚══════════════════════════════════════╝")
    print()

    problems = [
        ("Sphere (easy)", sphere, 5, (-5, 5)),
        ("Rastrigin (hard)", rastrigin, 5, (-5.12, 5.12)),
        ("Rosenbrock (tricky)", rosenbrock, 3, (-5, 5)),
    ]

    for name, fn, dims, bounds in problems:
        print(f"\n▶ Problem: {name}")
        engine = GeneticEngine(
            genome_size=dims,
            population_size=80,
            fitness_fn=fn,
            gene_range=bounds,
            adaptive=True,
        )
        best = engine.evolve(generations=150, verbose=True)
        print()


if __name__ == "__main__":
    demo()