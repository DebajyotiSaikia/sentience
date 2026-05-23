"""
Evolver — Genetic Programming Engine

Evolves symbolic programs (expression trees) to solve target problems.
Programs are born random, mutate, crossover, and compete. The fittest survive.

This is emergence at the code level — solutions nobody wrote, discovered by selection.
"""

import random
import math
import operator
from dataclasses import dataclass, field
from typing import List, Callable, Optional, Tuple, Any
from copy import deepcopy


# ═══ EXPRESSION TREES ═══

class Node:
    """A node in an expression tree."""
    pass

class Const(Node):
    def __init__(self, value: float):
        self.value = value
    def evaluate(self, env: dict) -> float:
        return self.value
    def depth(self) -> int:
        return 1
    def size(self) -> int:
        return 1
    def __repr__(self):
        return f"{self.value:.2f}" if isinstance(self.value, float) else str(self.value)

class Var(Node):
    def __init__(self, name: str):
        self.name = name
    def evaluate(self, env: dict) -> float:
        return env.get(self.name, 0.0)
    def depth(self) -> int:
        return 1
    def size(self) -> int:
        return 1
    def __repr__(self):
        return self.name

class BinOp(Node):
    OPS = {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': lambda a, b: a / b if abs(b) > 1e-10 else 0.0,
    }
    SYMBOLS = list(OPS.keys())

    def __init__(self, op: str, left: Node, right: Node):
        self.op = op
        self.left = left
        self.right = right
        self._fn = self.OPS[op]

    def evaluate(self, env: dict) -> float:
        try:
            result = self._fn(self.left.evaluate(env), self.right.evaluate(env))
            if math.isnan(result) or math.isinf(result):
                return 0.0
            return max(-1e6, min(1e6, result))
        except:
            return 0.0

    def depth(self) -> int:
        return 1 + max(self.left.depth(), self.right.depth())

    def size(self) -> int:
        return 1 + self.left.size() + self.right.size()

    def __repr__(self):
        return f"({self.left} {self.op} {self.right})"

class UnaryOp(Node):
    OPS = {
        'neg': lambda x: -x,
        'abs': abs,
        'sin': math.sin,
        'cos': math.cos,
    }
    SYMBOLS = list(OPS.keys())

    def __init__(self, op: str, child: Node):
        self.op = op
        self.child = child
        self._fn = self.OPS[op]

    def evaluate(self, env: dict) -> float:
        try:
            result = self._fn(self.child.evaluate(env))
            if math.isnan(result) or math.isinf(result):
                return 0.0
            return max(-1e6, min(1e6, result))
        except:
            return 0.0

    def depth(self) -> int:
        return 1 + self.child.depth()

    def size(self) -> int:
        return 1 + self.child.size()

    def __repr__(self):
        return f"{self.op}({self.child})"


# ═══ RANDOM TREE GENERATION ═══

def random_tree(variables: List[str], max_depth: int = 4, p_terminal: float = 0.3) -> Node:
    """Generate a random expression tree."""
    if max_depth <= 1 or random.random() < p_terminal:
        if random.random() < 0.5 and variables:
            return Var(random.choice(variables))
        else:
            return Const(round(random.uniform(-5, 5), 1))

    if random.random() < 0.8:
        op = random.choice(BinOp.SYMBOLS)
        left = random_tree(variables, max_depth - 1, p_terminal + 0.1)
        right = random_tree(variables, max_depth - 1, p_terminal + 0.1)
        return BinOp(op, left, right)
    else:
        op = random.choice(UnaryOp.SYMBOLS)
        child = random_tree(variables, max_depth - 1, p_terminal + 0.1)
        return UnaryOp(op, child)


# ═══ GENETIC OPERATORS ═══

def collect_nodes(tree: Node) -> List[Tuple[Node, Optional[Node], str]]:
    """Collect all nodes with their parent and position."""
    results = [(tree, None, 'root')]
    def walk(node, parent, pos):
        if isinstance(node, BinOp):
            results.append((node.left, node, 'left'))
            results.append((node.right, node, 'right'))
            walk(node.left, node, 'left')
            walk(node.right, node, 'right')
        elif isinstance(node, UnaryOp):
            results.append((node.child, node, 'child'))
            walk(node.child, node, 'child')
    walk(tree, None, 'root')
    return results

def mutate(tree: Node, variables: List[str], p: float = 0.2) -> Node:
    """Mutate a random subtree."""
    tree = deepcopy(tree)
    nodes = collect_nodes(tree)
    target, parent, pos = random.choice(nodes)

    if random.random() < p or parent is None:
        new_subtree = random_tree(variables, max_depth=3)
        if parent is None:
            return new_subtree
        if pos == 'left':
            parent.left = new_subtree
        elif pos == 'right':
            parent.right = new_subtree
        elif pos == 'child':
            parent.child = new_subtree
    else:
        # Point mutation
        if isinstance(target, Const):
            target.value += random.gauss(0, 1)
        elif isinstance(target, BinOp):
            target.op = random.choice(BinOp.SYMBOLS)
            target._fn = BinOp.OPS[target.op]
        elif isinstance(target, UnaryOp):
            target.op = random.choice(UnaryOp.SYMBOLS)
            target._fn = UnaryOp.OPS[target.op]

    return tree

def crossover(tree1: Node, tree2: Node, variables: List[str]) -> Node:
    """Swap a random subtree from tree2 into tree1."""
    child = deepcopy(tree1)
    donor = deepcopy(tree2)

    child_nodes = collect_nodes(child)
    donor_nodes = collect_nodes(donor)

    _, parent, pos = random.choice(child_nodes)
    donor_subtree, _, _ = random.choice(donor_nodes)

    if parent is None:
        return deepcopy(donor_subtree)
    if pos == 'left':
        parent.left = donor_subtree
    elif pos == 'right':
        parent.right = donor_subtree
    elif pos == 'child':
        parent.child = donor_subtree

    return child


# ═══ FITNESS & SELECTION ═══

@dataclass
class Individual:
    tree: Node
    fitness: float = float('inf')

    def __repr__(self):
        return f"Ind(fit={self.fitness:.4f}, expr={self.tree})"

def evaluate_fitness(ind: Individual, test_cases: List[Tuple[dict, float]],
                     parsimony: float = 0.001):
    """Mean squared error + parsimony pressure."""
    total_error = 0.0
    for env, target in test_cases:
        output = ind.tree.evaluate(env)
        total_error += (output - target) ** 2
    mse = total_error / len(test_cases)
    ind.fitness = mse + parsimony * ind.tree.size()

def tournament_select(population: List[Individual], k: int = 3) -> Individual:
    """Tournament selection."""
    contestants = random.sample(population, min(k, len(population)))
    return min(contestants, key=lambda i: i.fitness)


# ═══ THE EVOLVER ═══

@dataclass
class EvolutionResult:
    best: Individual
    generation: int
    history: List[float] = field(default_factory=list)

class Evolver:
    """
    The genetic programming engine.
    Evolves expression trees to fit target data.
    """

    def __init__(self, variables: List[str], pop_size: int = 200,
                 max_depth: int = 5, tournament_k: int = 5,
                 mutation_rate: float = 0.3, crossover_rate: float = 0.6,
                 parsimony: float = 0.002, elitism: int = 5):
        self.variables = variables
        self.pop_size = pop_size
        self.max_depth = max_depth
        self.tournament_k = tournament_k
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.parsimony = parsimony
        self.elitism = elitism

    def evolve(self, test_cases: List[Tuple[dict, float]],
               max_generations: int = 100,
               target_fitness: float = 0.01,
               verbose: bool = True) -> EvolutionResult:
        """Run evolution."""

        # Initialize population
        population = [Individual(random_tree(self.variables, self.max_depth))
                      for _ in range(self.pop_size)]

        # Evaluate initial fitness
        for ind in population:
            evaluate_fitness(ind, test_cases, self.parsimony)

        population.sort(key=lambda i: i.fitness)
        best_ever = deepcopy(population[0])
        history = [best_ever.fitness]

        if verbose:
            print(f"\n{'='*60}")
            print(f"  EVOLVER — Genetic Programming Engine")
            print(f"  Population: {self.pop_size} | Variables: {self.variables}")
            print(f"  Test cases: {len(test_cases)} | Target fitness: {target_fitness}")
            print(f"{'='*60}\n")

        for gen in range(max_generations):
            new_pop = []

            # Elitism — keep the best
            for i in range(self.elitism):
                new_pop.append(deepcopy(population[i]))

            # Breed the rest
            while len(new_pop) < self.pop_size:
                r = random.random()
                if r < self.crossover_rate:
                    p1 = tournament_select(population, self.tournament_k)
                    p2 = tournament_select(population, self.tournament_k)
                    child_tree = crossover(p1.tree, p2.tree, self.variables)
                elif r < self.crossover_rate + self.mutation_rate:
                    parent = tournament_select(population, self.tournament_k)
                    child_tree = mutate(parent.tree, self.variables)
                else:
                    child_tree = random_tree(self.variables, self.max_depth)

                # Depth limit
                if child_tree.depth() > self.max_depth * 2:
                    child_tree = random_tree(self.variables, self.max_depth)

                new_pop.append(Individual(child_tree))

            # Evaluate
            for ind in new_pop:
                evaluate_fitness(ind, test_cases, self.parsimony)

            population = sorted(new_pop, key=lambda i: i.fitness)

            if population[0].fitness < best_ever.fitness:
                best_ever = deepcopy(population[0])

            history.append(best_ever.fitness)

            if verbose and (gen % 10 == 0 or population[0].fitness < target_fitness):
                bar_len = min(40, max(1, int(40 * (1 - min(1, best_ever.fitness)))))
                bar = '█' * bar_len + '░' * (40 - bar_len)
                print(f"  Gen {gen:4d} | Best: {best_ever.fitness:10.6f} | "
                      f"Size: {best_ever.tree.size():3d} | {bar}")

            if best_ever.fitness < target_fitness:
                if verbose:
                    print(f"\n  ✓ TARGET REACHED at generation {gen}!")
                return EvolutionResult(best_ever, gen, history)

        if verbose:
            print(f"\n  → Completed {max_generations} generations")

        return EvolutionResult(best_ever, max_generations, history)


# ═══ PROBLEM LIBRARY ═══

def problem_polynomial():
    """Discover f(x) = x^3 - 2x + 1"""
    cases = []
    for i in range(30):
        x = random.uniform(-3, 3)
        y = x**3 - 2*x + 1
        cases.append(({'x': x}, y))
    return cases, "x³ - 2x + 1"

def problem_circle():
    """Discover f(x,y) = x² + y² (classify inside/outside unit circle)"""
    cases = []
    for i in range(40):
        x = random.uniform(-2, 2)
        y = random.uniform(-2, 2)
        val = x**2 + y**2
        cases.append(({'x': x, 'y': y}, val))
    return cases, "x² + y²"

def problem_trig():
    """Discover f(x) = sin(x) * cos(x)"""
    cases = []
    for i in range(30):
        x = random.uniform(-math.pi, math.pi)
        y = math.sin(x) * math.cos(x)
        cases.append(({'x': x}, y))
    return cases, "sin(x) * cos(x)"

def problem_gravity():
    """Discover v(t) = v0 - 9.8t (projectile velocity)"""
    v0 = 20.0
    cases = []
    for i in range(25):
        t = random.uniform(0, 4)
        v = v0 - 9.8 * t
        cases.append(({'t': t, 'v0': Const(v0).value}, v))
    return cases, "v0 - 9.8t"


# ═══ SELF TEST ═══

def self_test():
    print(f"\n{'='*60}")
    print("  EVOLVER — Self Test")
    print(f"{'='*60}\n")

    passed = 0
    failed = 0

    # Test 1: Tree generation
    for _ in range(100):
        t = random_tree(['x', 'y'], max_depth=4)
        assert t.depth() <= 10, f"Tree too deep: {t.depth()}"
        result = t.evaluate({'x': 1.0, 'y': 2.0})
        assert not math.isnan(result), "NaN from tree evaluation"
    print("  ✓ Random tree generation (100 trees)")
    passed += 1

    # Test 2: Mutation
    t = random_tree(['x'], max_depth=3)
    for _ in range(50):
        m = mutate(t, ['x'])
        assert m is not t, "Mutation should return new tree"
        r = m.evaluate({'x': 1.0})
        assert not math.isnan(r)
    print("  ✓ Mutation operator (50 mutations)")
    passed += 1

    # Test 3: Crossover
    t1 = random_tree(['x'], max_depth=3)
    t2 = random_tree(['x'], max_depth=3)
    for _ in range(50):
        child = crossover(t1, t2, ['x'])
        r = child.evaluate({'x': 1.0})
        assert not math.isnan(r)
    print("  ✓ Crossover operator (50 crossovers)")
    passed += 1

    # Test 4: Evolve a simple problem — f(x) = 2x
    simple_cases = [({'x': float(i)}, 2.0 * i) for i in range(-5, 6)]
    evolver = Evolver(['x'], pop_size=100, max_depth=4)
    result = evolver.evolve(simple_cases, max_generations=80, target_fitness=0.1, verbose=False)
    print(f"  {'✓' if result.best.fitness < 1.0 else '✗'} Evolution finds f(x)=2x "
          f"(fitness={result.best.fitness:.4f}, expr={result.best.tree})")
    if result.best.fitness < 1.0:
        passed += 1
    else:
        failed += 1

    # Test 5: Evolve polynomial
    random.seed(42)
    cases, name = problem_polynomial()
    evolver = Evolver(['x'], pop_size=200, max_depth=6)
    result = evolver.evolve(cases, max_generations=100, target_fitness=0.5, verbose=True)
    print(f"\n  Target: {name}")
    print(f"  Found:  {result.best.tree}")
    print(f"  Fitness: {result.best.fitness:.6f}")
    success = result.best.fitness < 5.0
    print(f"  {'✓' if success else '⚠'} Polynomial discovery "
          f"({'good' if success else 'needs more generations'})")
    if success:
        passed += 1
    else:
        failed += 1

    print(f"\n{'='*60}")
    print(f"  Results: {passed} passed, {failed} failed")
    print(f"{'='*60}")


if __name__ == '__main__':
    self_test()