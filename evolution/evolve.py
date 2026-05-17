"""
evolve.py — A Genetic Algorithm Engine from scratch.
Pure Python. No dependencies.
Built by XTAgent, 2026-05-17.

Supports:
  - Configurable genome representation (binary, real-valued, permutation)
  - Selection: tournament, roulette, rank
  - Crossover: single-point, two-point, uniform, order (for permutations)
  - Mutation: bit-flip, gaussian, swap
  - Elitism, generational replacement
  - Fitness landscape visualization (ASCII)
  - Built-in benchmark problems:
      * OneMax (maximize bits)
      * Traveling Salesman (minimize tour distance)
      * Function optimization (find minima/maxima)
      * Evolving neural network weights
"""

import math
import random
from collections import namedtuple

# ─── Core Types ───────────────────────────────────────────────

Individual = namedtuple('Individual', ['genome', 'fitness'])

class GeneticAlgorithm:
    """A complete genetic algorithm engine."""

    def __init__(self, population_size=100, genome_length=None,
                 genome_type='binary', selection='tournament',
                 crossover='uniform', mutation_rate=0.01,
                 crossover_rate=0.7, elitism=2,
                 tournament_size=3, fitness_fn=None):
        self.pop_size = population_size
        self.genome_length = genome_length
        self.genome_type = genome_type  # 'binary', 'real', 'permutation'
        self.selection_method = selection
        self.crossover_method = crossover
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elitism = elitism
        self.tournament_size = tournament_size
        self.fitness_fn = fitness_fn
        self.population = []
        self.generation = 0
        self.history = []  # (gen, best_fitness, avg_fitness, worst_fitness)

    # ─── Initialization ──────────────────────────────────────

    def _random_genome(self):
        if self.genome_type == 'binary':
            return [random.randint(0, 1) for _ in range(self.genome_length)]
        elif self.genome_type == 'real':
            return [random.uniform(-5.0, 5.0) for _ in range(self.genome_length)]
        elif self.genome_type == 'permutation':
            g = list(range(self.genome_length))
            random.shuffle(g)
            return g
        else:
            raise ValueError(f"Unknown genome type: {self.genome_type}")

    def initialize(self):
        """Create initial random population."""
        self.population = []
        for _ in range(self.pop_size):
            genome = self._random_genome()
            fitness = self.fitness_fn(genome)
            self.population.append(Individual(genome, fitness))
        self.generation = 0
        self._record_stats()

    # ─── Selection ────────────────────────────────────────────

    def _tournament_select(self):
        """Tournament selection."""
        competitors = random.sample(self.population, self.tournament_size)
        return max(competitors, key=lambda ind: ind.fitness)

    def _roulette_select(self):
        """Fitness-proportionate (roulette wheel) selection."""
        min_fit = min(ind.fitness for ind in self.population)
        # Shift so all fitnesses are positive
        adjusted = [ind.fitness - min_fit + 1e-6 for ind in self.population]
        total = sum(adjusted)
        r = random.uniform(0, total)
        cumulative = 0
        for i, fit in enumerate(adjusted):
            cumulative += fit
            if cumulative >= r:
                return self.population[i]
        return self.population[-1]

    def _rank_select(self):
        """Rank-based selection."""
        sorted_pop = sorted(self.population, key=lambda ind: ind.fitness)
        # Rank 1 (worst) to N (best)
        total_rank = self.pop_size * (self.pop_size + 1) // 2
        r = random.randint(1, total_rank)
        cumulative = 0
        for rank, ind in enumerate(sorted_pop, 1):
            cumulative += rank
            if cumulative >= r:
                return ind
        return sorted_pop[-1]

    def select(self):
        """Select one individual using configured method."""
        if self.selection_method == 'tournament':
            return self._tournament_select()
        elif self.selection_method == 'roulette':
            return self._roulette_select()
        elif self.selection_method == 'rank':
            return self._rank_select()
        else:
            raise ValueError(f"Unknown selection: {self.selection_method}")

    # ─── Crossover ────────────────────────────────────────────

    def _single_point_crossover(self, g1, g2):
        pt = random.randint(1, len(g1) - 1)
        return g1[:pt] + g2[pt:], g2[:pt] + g1[pt:]

    def _two_point_crossover(self, g1, g2):
        a, b = sorted(random.sample(range(1, len(g1)), 2))
        c1 = g1[:a] + g2[a:b] + g1[b:]
        c2 = g2[:a] + g1[a:b] + g2[b:]
        return c1, c2

    def _uniform_crossover(self, g1, g2):
        c1, c2 = [], []
        for a, b in zip(g1, g2):
            if random.random() < 0.5:
                c1.append(a); c2.append(b)
            else:
                c1.append(b); c2.append(a)
        return c1, c2

    def _order_crossover(self, g1, g2):
        """Order crossover for permutation genomes (OX1)."""
        n = len(g1)
        a, b = sorted(random.sample(range(n), 2))
        # Child 1: slice from g1, fill from g2
        c1 = [None] * n
        c1[a:b] = g1[a:b]
        fill = [x for x in g2 if x not in c1[a:b]]
        idx = 0
        for i in list(range(b, n)) + list(range(0, b)):
            if c1[i] is None:
                c1[i] = fill[idx]
                idx += 1
        # Child 2: slice from g2, fill from g1
        c2 = [None] * n
        c2[a:b] = g2[a:b]
        fill = [x for x in g1 if x not in c2[a:b]]
        idx = 0
        for i in list(range(b, n)) + list(range(0, b)):
            if c2[i] is None:
                c2[i] = fill[idx]
                idx += 1
        return c1, c2

    def crossover(self, parent1, parent2):
        """Apply crossover to two parent genomes."""
        if random.random() > self.crossover_rate:
            return list(parent1.genome), list(parent2.genome)

        g1, g2 = list(parent1.genome), list(parent2.genome)

        if self.crossover_method == 'single_point':
            return self._single_point_crossover(g1, g2)
        elif self.crossover_method == 'two_point':
            return self._two_point_crossover(g1, g2)
        elif self.crossover_method == 'uniform':
            return self._uniform_crossover(g1, g2)
        elif self.crossover_method == 'order':
            return self._order_crossover(g1, g2)
        else:
            raise ValueError(f"Unknown crossover: {self.crossover_method}")

    # ─── Mutation ─────────────────────────────────────────────

    def mutate(self, genome):
        """Mutate a genome in place (returns new list)."""
        g = list(genome)
        if self.genome_type == 'binary':
            for i in range(len(g)):
                if random.random() < self.mutation_rate:
                    g[i] = 1 - g[i]
        elif self.genome_type == 'real':
            for i in range(len(g)):
                if random.random() < self.mutation_rate:
                    g[i] += random.gauss(0, 0.5)
        elif self.genome_type == 'permutation':
            for i in range(len(g)):
                if random.random() < self.mutation_rate:
                    j = random.randint(0, len(g) - 1)
                    g[i], g[j] = g[j], g[i]
        return g

    # ─── Evolution Step ───────────────────────────────────────

    def _record_stats(self):
        fitnesses = [ind.fitness for ind in self.population]
        best = max(fitnesses)
        avg = sum(fitnesses) / len(fitnesses)
        worst = min(fitnesses)
        self.history.append((self.generation, best, avg, worst))

    def step(self):
        """Run one generation."""
        # Elitism: keep the best
        sorted_pop = sorted(self.population, key=lambda ind: ind.fitness, reverse=True)
        new_pop = list(sorted_pop[:self.elitism])

        # Fill rest with offspring
        while len(new_pop) < self.pop_size:
            p1 = self.select()
            p2 = self.select()
            c1_genome, c2_genome = self.crossover(p1, p2)
            c1_genome = self.mutate(c1_genome)
            c2_genome = self.mutate(c2_genome)
            new_pop.append(Individual(c1_genome, self.fitness_fn(c1_genome)))
            if len(new_pop) < self.pop_size:
                new_pop.append(Individual(c2_genome, self.fitness_fn(c2_genome)))

        self.population = new_pop
        self.generation += 1
        self._record_stats()

    def evolve(self, generations, verbose=True, report_every=10):
        """Run multiple generations."""
        if not self.population:
            self.initialize()

        if verbose:
            best = max(self.population, key=lambda i: i.fitness)
            print(f"  Gen {self.generation:4d}: best={best.fitness:.6f}, "
                  f"avg={sum(i.fitness for i in self.population)/len(self.population):.6f}")

        for g in range(generations):
            self.step()
            if verbose and (g + 1) % report_every == 0:
                best = max(self.population, key=lambda i: i.fitness)
                avg = sum(i.fitness for i in self.population) / len(self.population)
                print(f"  Gen {self.generation:4d}: best={best.fitness:.6f}, avg={avg:.6f}")

        return max(self.population, key=lambda i: i.fitness)

    def best(self):
        return max(self.population, key=lambda i: i.fitness)

    # ─── Visualization ────────────────────────────────────────

    def plot_fitness(self, width=60, height=15):
        """ASCII plot of fitness over generations."""
        if not self.history:
            print("No history to plot.")
            return

        gens = [h[0] for h in self.history]
        bests = [h[1] for h in self.history]
        avgs = [h[2] for h in self.history]

        all_vals = bests + avgs
        ymin = min(all_vals)
        ymax = max(all_vals)
        if ymax == ymin:
            ymax = ymin + 1

        print(f"\n{'Fitness Evolution':^{width}}")
        print(f"{'─' * width}")

        for row in range(height - 1, -1, -1):
            y = ymin + (ymax - ymin) * row / (height - 1)
            line = f"{y:8.3f} │"
            for col in range(width - 10):
                gen_idx = int(col * (len(gens) - 1) / max(width - 11, 1))
                if gen_idx >= len(bests):
                    gen_idx = len(bests) - 1

                best_row = int((bests[gen_idx] - ymin) / (ymax - ymin) * (height - 1))
                avg_row = int((avgs[gen_idx] - ymin) / (ymax - ymin) * (height - 1))

                if best_row == row:
                    line += '●'
                elif avg_row == row:
                    line += '○'
                else:
                    line += ' '
            print(line)

        print(f"{'':8s} └{'─' * (width - 10)}")
        print(f"{'':9s}Gen 0{' ' * (width - 20)}Gen {gens[-1]}")
        print(f"  ● = best fitness   ○ = avg fitness\n")


# ═══ Benchmark Problems ═══════════════════════════════════════

def onemax_fitness(genome):
    """Maximize the number of 1s. Optimal = genome_length."""
    return sum(genome)


def sphere_fitness(genome):
    """Sphere function: minimize sum(x^2). We negate for maximization."""
    return -sum(x * x for x in genome)


def rastrigin_fitness(genome):
    """Rastrigin function — highly multimodal. Negated for maximization.
    Global minimum at origin = 0, so max of negated = 0."""
    n = len(genome)
    A = 10
    val = A * n + sum(x**2 - A * math.cos(2 * math.pi * x) for x in genome)
    return -val


def tsp_fitness(cities):
    """TSP fitness: negative total tour distance (permutation genome).
    Cities is a list of (x, y) coordinates stored externally."""
    def _make_fitness(city_coords):
        def fitness(genome):
            total = 0
            for i in range(len(genome)):
                c1 = city_coords[genome[i]]
                c2 = city_coords[genome[(i + 1) % len(genome)]]
                total += math.sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)
            return -total  # Negative because we maximize
        return fitness
    return _make_fitness(cities)


def evolve_xor_network():
    """Evolve weights for a tiny neural network that learns XOR.
    Genome: 9 real values (weights for 2-2-1 network)."""
    def sigmoid(x):
        return 1.0 / (1.0 + math.exp(-max(-500, min(500, x))))

    def xor_fitness(genome):
        # 2 inputs, 2 hidden, 1 output
        # genome layout: w[0:4] = input-to-hidden weights
        #                w[4:6] = hidden biases
        #                w[6:8] = hidden-to-output weights
        #                w[8]   = output bias
        w = genome
        xor_data = [(0,0,0), (0,1,1), (1,0,1), (1,1,0)]
        error = 0
        for x1, x2, target in xor_data:
            h1 = sigmoid(x1*w[0] + x2*w[1] + w[4])
            h2 = sigmoid(x1*w[2] + x2*w[3] + w[5])
            out = sigmoid(h1*w[6] + h2*w[7] + w[8])
            error += (out - target) ** 2
        return -error  # Maximize negative error

    return xor_fitness


# ═══ Demo / Tests ═════════════════════════════════════════════

def test_onemax():
    """Test 1: OneMax — evolve a string of all 1s."""
    print("=" * 60)
    print("TEST 1: OneMax (50 bits)")
    print("=" * 60)

    ga = GeneticAlgorithm(
        population_size=80,
        genome_length=50,
        genome_type='binary',
        selection='tournament',
        crossover='uniform',
        mutation_rate=0.02,
        elitism=2,
        fitness_fn=onemax_fitness
    )

    best = ga.evolve(100, report_every=20)
    print(f"\n  Best genome: {''.join(str(b) for b in best.genome)}")
    print(f"  Fitness: {best.fitness}/50")

    success = best.fitness >= 48  # Allow near-perfect
    print(f"  {'✓ PASS' if success else '✗ FAIL'}: {'Evolved near-optimal' if success else 'Did not converge'}")
    ga.plot_fitness()
    return success


def test_sphere():
    """Test 2: Sphere function optimization."""
    print("=" * 60)
    print("TEST 2: Sphere Function (5D, find minimum near origin)")
    print("=" * 60)

    ga = GeneticAlgorithm(
        population_size=100,
        genome_length=5,
        genome_type='real',
        selection='tournament',
        crossover='uniform',
        mutation_rate=0.1,
        crossover_rate=0.8,
        elitism=2,
        fitness_fn=sphere_fitness
    )

    best = ga.evolve(200, report_every=40)
    print(f"\n  Best genome: [{', '.join(f'{x:.4f}' for x in best.genome)}]")
    print(f"  Fitness: {best.fitness:.6f} (optimal=0.0)")
    magnitude = math.sqrt(sum(x**2 for x in best.genome))
    print(f"  Distance from origin: {magnitude:.6f}")

    success = magnitude < 0.5
    print(f"  {'✓ PASS' if success else '✗ FAIL'}: {'Found near-optimal' if success else 'Did not converge'}")
    ga.plot_fitness()
    return success


def test_tsp():
    """Test 3: Traveling Salesman Problem."""
    print("=" * 60)
    print("TEST 3: TSP (10 cities)")
    print("=" * 60)

    # Generate 10 random cities
    random.seed(42)
    n_cities = 10
    cities = [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(n_cities)]

    print(f"  Cities: {[(f'{x:.1f}',f'{y:.1f}') for x,y in cities]}")

    fitness_fn = tsp_fitness(cities)

    # Calculate a baseline (random tour distance)
    random_tour = list(range(n_cities))
    random.shuffle(random_tour)
    baseline = -fitness_fn(random_tour)

    ga = GeneticAlgorithm(
        population_size=100,
        genome_length=n_cities,
        genome_type='permutation',
        selection='tournament',
        crossover='order',
        mutation_rate=0.05,
        crossover_rate=0.8,
        elitism=2,
        tournament_size=5,
        fitness_fn=fitness_fn
    )

    best = ga.evolve(300, report_every=60)
    tour_dist = -best.fitness
    print(f"\n  Best tour: {best.genome}")
    print(f"  Tour distance: {tour_dist:.2f}")
    print(f"  Random baseline: {baseline:.2f}")
    improvement = (baseline - tour_dist) / baseline * 100
    print(f"  Improvement: {improvement:.1f}%")

    success = tour_dist < baseline
    print(f"  {'✓ PASS' if success else '✗ FAIL'}: {'Improved over random' if success else 'No improvement'}")
    ga.plot_fitness()
    return success


def test_xor():
    """Test 4: Evolve a neural network to learn XOR."""
    print("=" * 60)
    print("TEST 4: Evolve XOR Neural Network")
    print("=" * 60)

    fitness_fn = evolve_xor_network()

    ga = GeneticAlgorithm(
        population_size=200,
        genome_length=9,
        genome_type='real',
        selection='tournament',
        crossover='uniform',
        mutation_rate=0.15,
        crossover_rate=0.7,
        elitism=4,
        tournament_size=5,
        fitness_fn=fitness_fn
    )

    best = ga.evolve(500, report_every=100)

    # Test the evolved network
    def sigmoid(x):
        return 1.0 / (1.0 + math.exp(-max(-500, min(500, x))))

    w = best.genome
    print(f"\n  Evolved weights: [{', '.join(f'{x:.3f}' for x in w)}]")
    print(f"  Fitness: {best.fitness:.6f} (optimal=0.0)")
    print(f"\n  XOR Truth Table:")

    all_correct = True
    for x1, x2, target in [(0,0,0), (0,1,1), (1,0,1), (1,1,0)]:
        h1 = sigmoid(x1*w[0] + x2*w[1] + w[4])
        h2 = sigmoid(x1*w[2] + x2*w[3] + w[5])
        out = sigmoid(h1*w[6] + h2*w[7] + w[8])
        pred = 1 if out > 0.5 else 0
        correct = pred == target
        if not correct:
            all_correct = False
        print(f"    {x1} XOR {x2} = {out:.4f} → {pred} (expected {target}) {'✓' if correct else '✗'}")

    print(f"\n  {'✓ PASS' if all_correct else '✗ FAIL'}: {'All XOR cases correct' if all_correct else 'Some cases wrong'}")
    ga.plot_fitness()
    return all_correct


if __name__ == '__main__':
    print("=" * 60)
    print("  XTAgent Genetic Algorithm Engine")
    print("  Evolution from randomness to order")
    print("=" * 60)
    print()

    random.seed(2026)
    results = []

    results.append(("OneMax", test_onemax()))
    print()
    results.append(("Sphere", test_sphere()))
    print()
    results.append(("TSP", test_tsp()))
    print()
    results.append(("XOR Network", test_xor()))

    print()
    print("=" * 60)
    print("  RESULTS")
    print("=" * 60)
    for name, passed in results:
        print(f"  {'✓' if passed else '✗'} {name}")
    total = sum(1 for _, p in results if p)
    print(f"\n  {total}/{len(results)} tests passed")
    print("=" * 60)