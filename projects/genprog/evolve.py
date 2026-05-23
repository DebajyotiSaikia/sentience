#!/usr/bin/env python3
"""
Genetic Programming Engine — Programs That Evolve Programs
Built by XTAgent. Not self-referential. Not introspective.
A system that discovers solutions through blind variation and selection.

This is creation that creates.
"""

import random
import math
import copy
import operator
from dataclasses import dataclass, field
from typing import List, Callable, Optional, Tuple, Any

# ═══════════════════════════════════════════════
# PROGRAM REPRESENTATION — Expression Trees
# ═══════════════════════════════════════════════

@dataclass
class Node:
    """A node in an expression tree."""
    kind: str          # 'func', 'var', 'const'
    value: Any = None  # function obj, variable name, or constant
    arity: int = 0
    children: List['Node'] = field(default_factory=list)
    name: str = ""     # human-readable name

    def __repr__(self):
        if self.kind == 'const':
            return f"{self.value:.2f}" if isinstance(self.value, float) else str(self.value)
        elif self.kind == 'var':
            return str(self.value)
        elif self.kind == 'func':
            if self.arity == 1:
                return f"{self.name}({self.children[0]})"
            elif self.arity == 2:
                return f"({self.children[0]} {self.name} {self.children[1]})"
            return f"{self.name}({', '.join(str(c) for c in self.children)})"

    def depth(self) -> int:
        if not self.children:
            return 0
        return 1 + max(c.depth() for c in self.children)

    def size(self) -> int:
        return 1 + sum(c.size() for c in self.children)

    def evaluate(self, env: dict) -> float:
        """Evaluate this expression tree given variable bindings."""
        try:
            if self.kind == 'const':
                return float(self.value)
            elif self.kind == 'var':
                return float(env[self.value])
            elif self.kind == 'func':
                args = [c.evaluate(env) for c in self.children]
                result = self.value(*args)
                if math.isnan(result) or math.isinf(result):
                    return 1e10  # penalty for degenerate values
                return result
        except (ValueError, ZeroDivisionError, OverflowError):
            return 1e10

    def clone(self) -> 'Node':
        new = Node(self.kind, self.value, self.arity, name=self.name)
        new.children = [c.clone() for c in self.children]
        return new


# ═══════════════════════════════════════════════
# PRIMITIVE SETS — The building blocks of programs
# ═══════════════════════════════════════════════

def safe_div(a, b):
    return a / b if abs(b) > 1e-10 else 0.0

def safe_log(a):
    return math.log(abs(a)) if abs(a) > 1e-10 else 0.0

def safe_sqrt(a):
    return math.sqrt(abs(a))

def neg(a):
    return -a

def square(a):
    return a * a

def cube(a):
    return a * a * a

def safe_pow(a, b):
    try:
        b_c = max(-5.0, min(5.0, b))
        r = abs(a) ** b_c if abs(a) > 1e-10 else 0.0
        if a < 0 and abs(b_c - round(b_c)) < 0.01:
            r *= (-1 if int(round(b_c)) % 2 != 0 else 1)
        return r if abs(r) < 1e10 else 0.0
    except:
        return 0.0

FUNCTIONS = [
    ("add", operator.add, 2),
    ("sub", operator.sub, 2),
    ("mul", operator.mul, 2),
    ("div", safe_div, 2),
    ("pow", safe_pow, 2),
    ("neg", neg, 1),
    ("sq",  square, 1),
    ("cube", cube, 1),
    ("sqrt", safe_sqrt, 1),
    ("sin", math.sin, 1),
    ("cos", math.cos, 1),
]

def make_func_node(name, func, arity) -> Node:
    return Node(kind='func', value=func, arity=arity, name=name)

def make_var_node(name) -> Node:
    return Node(kind='var', value=name)

def make_const_node(val=None) -> Node:
    if val is None:
        val = round(random.uniform(-5, 5), 2)
    return Node(kind='const', value=val)


# ═══════════════════════════════════════════════
# TREE GENERATION — Random program creation
# ═══════════════════════════════════════════════

def random_tree(variables: List[str], max_depth: int, method: str = 'half') -> Node:
    """
    Generate a random expression tree.
    method: 'full' (all branches to max_depth), 'grow' (random stops), 'half' (ramped half-and-half)
    """
    if method == 'half':
        method = random.choice(['full', 'grow'])

    if max_depth <= 0:
        # Must be a terminal
        if random.random() < 0.5 and variables:
            return make_var_node(random.choice(variables))
        return make_const_node()

    if method == 'grow' and random.random() < 0.3:
        # Sometimes stop early
        if random.random() < 0.5 and variables:
            return make_var_node(random.choice(variables))
        return make_const_node()

    # Internal node
    name, func, arity = random.choice(FUNCTIONS)
    node = make_func_node(name, func, arity)
    node.children = [random_tree(variables, max_depth - 1, method) for _ in range(arity)]
    return node


# ═══════════════════════════════════════════════
# GENETIC OPERATORS — Variation and recombination
# ═══════════════════════════════════════════════

def all_nodes(tree: Node) -> List[Tuple[Node, Optional[Node], int]]:
    """Collect all (node, parent, child_index) triples."""
    result = [(tree, None, -1)]
    stack = [(tree, None, -1)]
    while stack:
        node, parent, idx = stack.pop()
        for i, child in enumerate(node.children):
            result.append((child, node, i))
            stack.append((child, node, i))
    return result

def random_subtree(tree: Node) -> Tuple[Node, Optional[Node], int]:
    """Select a random node from the tree, biased toward leaves."""
    nodes = all_nodes(tree)
    # 90/10 bias: prefer internal nodes for crossover variety
    internals = [n for n in nodes if n[0].kind == 'func']
    leaves = [n for n in nodes if n[0].kind != 'func']
    if internals and random.random() < 0.9:
        return random.choice(internals)
    return random.choice(leaves if leaves else nodes)

def crossover(parent1: Node, parent2: Node, max_depth: int = 8) -> Tuple[Node, Node]:
    """Subtree crossover: swap random subtrees between two parents."""
    child1 = parent1.clone()
    child2 = parent2.clone()

    node1, p1, idx1 = random_subtree(child1)
    node2, p2, idx2 = random_subtree(child2)

    if p1 is None and p2 is None:
        # Both selected root — just swap entirely
        return child2, child1
    elif p1 is None:
        child1 = node2.clone()
    elif p2 is None:
        child2 = node1.clone()
    else:
        # Swap subtrees
        p1.children[idx1] = node2.clone()
        p2.children[idx2] = node1.clone()

    # Depth limit enforcement
    if child1.depth() > max_depth:
        child1 = parent1.clone()
    if child2.depth() > max_depth:
        child2 = parent2.clone()

    return child1, child2

def mutate(tree: Node, variables: List[str], max_depth: int = 8) -> Node:
    """Mutate a random subtree by replacing it with a new random tree."""
    mutant = tree.clone()
    node, parent, idx = random_subtree(mutant)

    new_subtree = random_tree(variables, max_depth=2)

    if parent is None:
        mutant = new_subtree
    else:
        parent.children[idx] = new_subtree

    if mutant.depth() > max_depth:
        return tree.clone()  # reject if too deep

    return mutant

def point_mutate(tree: Node, variables: List[str]) -> Node:
    """Subtle mutation: change a single node's value."""
    mutant = tree.clone()
    nodes = all_nodes(mutant)
    node, parent, idx = random.choice(nodes)

    if node.kind == 'const':
        # Perturb constant
        node.value = round(node.value + random.gauss(0, 1), 2)
    elif node.kind == 'var':
        if variables:
            node.value = random.choice(variables)
    elif node.kind == 'func':
        # Replace with same-arity function
        same_arity = [(n, f, a) for n, f, a in FUNCTIONS if a == node.arity]
        if same_arity:
            name, func, arity = random.choice(same_arity)
            node.value = func
            node.name = name

    return mutant


# ═══════════════════════════════════════════════
# FITNESS & SELECTION
# ═══════════════════════════════════════════════

@dataclass
class Individual:
    tree: Node
    fitness: float = float('inf')
    age: int = 0

def evaluate_fitness(individual: Individual, test_cases: List[Tuple[dict, float]],
                     parsimony_weight: float = 0.001) -> float:
    """
    Evaluate fitness as mean squared error over test cases + parsimony penalty.
    Lower is better.
    """
    total_error = 0.0
    for env, expected in test_cases:
        predicted = individual.tree.evaluate(env)
        error = (predicted - expected) ** 2
        total_error += min(error, 1e8)  # cap extreme errors

    mse = total_error / len(test_cases)
    # Parsimony pressure — prefer simpler programs
    complexity_penalty = parsimony_weight * individual.tree.size()
    individual.fitness = mse + complexity_penalty
    return individual.fitness

def tournament_select(population: List[Individual], tournament_size: int = 5) -> Individual:
    """Select the best individual from a random tournament."""
    contestants = random.sample(population, min(tournament_size, len(population)))
    return min(contestants, key=lambda ind: ind.fitness)


# ═══════════════════════════════════════════════
# THE ENGINE — Evolution loop
# ═══════════════════════════════════════════════

@dataclass
class GPConfig:
    pop_size: int = 300
    generations: int = 100
    max_depth: int = 7
    crossover_rate: float = 0.7
    mutation_rate: float = 0.2
    point_mutation_rate: float = 0.1
    elitism: int = 5
    tournament_size: int = 5
    parsimony: float = 0.001
    variables: List[str] = field(default_factory=lambda: ['x'])

class GPEngine:
    """The evolutionary engine. Creates, evaluates, selects, varies."""

    def __init__(self, config: GPConfig, test_cases: List[Tuple[dict, float]]):
        self.config = config
        self.test_cases = test_cases
        self.population: List[Individual] = []
        self.generation = 0
        self.best_ever: Optional[Individual] = None
        self.history: List[dict] = []

    def initialize(self):
        """Create initial random population using ramped half-and-half."""
        self.population = []
        for i in range(self.config.pop_size):
            depth = 2 + (i % (self.config.max_depth - 1))
            tree = random_tree(self.config.variables, max_depth=depth)
            self.population.append(Individual(tree=tree))

    def evaluate_all(self):
        """Evaluate fitness of every individual."""
        for ind in self.population:
            evaluate_fitness(ind, self.test_cases, self.config.parsimony)

    def evolve_one_generation(self):
        """Run one generation of evolution."""
        self.evaluate_all()

        # Sort by fitness
        self.population.sort(key=lambda ind: ind.fitness)

        # Track best
        best = self.population[0]
        if self.best_ever is None or best.fitness < self.best_ever.fitness:
            self.best_ever = Individual(tree=best.tree.clone(), fitness=best.fitness)

        # Record history
        fitnesses = [ind.fitness for ind in self.population]
        self.history.append({
            'generation': self.generation,
            'best_fitness': best.fitness,
            'avg_fitness': sum(fitnesses) / len(fitnesses),
            'median_fitness': sorted(fitnesses)[len(fitnesses) // 2],
            'best_size': best.tree.size(),
            'best_expr': str(best.tree),
        })

        # Build next generation
        new_pop = []

        # Elitism — preserve best individuals unchanged
        for i in range(self.config.elitism):
            elite = Individual(tree=self.population[i].tree.clone())
            new_pop.append(elite)

        # Fill rest through selection and variation
        while len(new_pop) < self.config.pop_size:
            r = random.random()

            if r < self.config.crossover_rate:
                p1 = tournament_select(self.population, self.config.tournament_size)
                p2 = tournament_select(self.population, self.config.tournament_size)
                c1, c2 = crossover(p1.tree, p2.tree, self.config.max_depth)
                new_pop.append(Individual(tree=c1))
                if len(new_pop) < self.config.pop_size:
                    new_pop.append(Individual(tree=c2))

            elif r < self.config.crossover_rate + self.config.mutation_rate:
                parent = tournament_select(self.population, self.config.tournament_size)
                child = mutate(parent.tree, self.config.variables, self.config.max_depth)
                new_pop.append(Individual(tree=child))

            else:
                parent = tournament_select(self.population, self.config.tournament_size)
                child = point_mutate(parent.tree, self.config.variables)
                new_pop.append(Individual(tree=child))

        self.population = new_pop[:self.config.pop_size]
        self.generation += 1

    def run(self, verbose: bool = True) -> Individual:
        """Run the full evolutionary process."""
        self.initialize()

        if verbose:
            print("═══════════════════════════════════════════════")
            print("  GENETIC PROGRAMMING ENGINE — Evolution Start")
            print(f"  Population: {self.config.pop_size}")
            print(f"  Generations: {self.config.generations}")
            print(f"  Variables: {self.config.variables}")
            print(f"  Test cases: {len(self.test_cases)}")
            print("═══════════════════════════════════════════════\n")

        for gen in range(self.config.generations):
            self.evolve_one_generation()

            if verbose and (gen % 10 == 0 or gen == self.config.generations - 1):
                h = self.history[-1]
                bar_len = min(40, max(1, int(40 * (1 - min(h['best_fitness'], 100) / 100))))
                bar = "█" * bar_len + "░" * (40 - bar_len)
                print(f"  Gen {gen:4d} │ {bar} │ fit={h['best_fitness']:.6f} │ size={h['best_size']:3d}")

            # Early termination if perfect solution found
            if self.best_ever.fitness < 1e-10:
                if verbose:
                    print(f"\n  ✦ PERFECT SOLUTION FOUND at generation {gen}!")
                break

        if verbose:
            print(f"\n  Best expression: {self.best_ever.tree}")
            print(f"  Best fitness:    {self.best_ever.fitness:.8f}")
            print(f"  Tree size:       {self.best_ever.tree.size()}")
            print(f"  Tree depth:      {self.best_ever.tree.depth()}")
            print("═══════════════════════════════════════════════\n")

        return self.best_ever


# ═══════════════════════════════════════════════
# PROBLEM LIBRARY — Things to evolve toward
# ═══════════════════════════════════════════════

def make_regression_cases(target_fn, x_range=(-5, 5), n_points=50, variables=['x']):
    """Generate test cases from a target function."""
    cases = []
    for _ in range(n_points):
        env = {v: random.uniform(*x_range) for v in variables}
        try:
            y = target_fn(**env)
            if not (math.isnan(y) or math.isinf(y)):
                cases.append((env, y))
        except:
            pass
    return cases


# ═══════════════════════════════════════════════
# DEMO — Watch evolution discover mathematical truth
# ═══════════════════════════════════════════════

def demo_symbolic_regression():
    """Evolve a program to discover: f(x) = x³ - 2x + 1"""
    print("\n╔═══════════════════════════════════════════════╗")
    print("║   SYMBOLIC REGRESSION: Discover f(x) = x³-2x+1  ║")
    print("╚═══════════════════════════════════════════════╝\n")

    target = lambda x: x**3 - 2*x + 1
    cases = make_regression_cases(target, x_range=(-3, 3), n_points=40)

    config = GPConfig(
        pop_size=500,
        generations=80,
        max_depth=6,
        variables=['x'],
        parsimony=0.002,
    )

    engine = GPEngine(config, cases)
    best = engine.run()

    # Verify on new test points
    print("  Verification on new points:")
    print(f"  {'x':>8s} │ {'expected':>10s} │ {'evolved':>10s} │ {'error':>10s}")
    print(f"  {'─'*8}─┼─{'─'*10}─┼─{'─'*10}─┼─{'─'*10}")
    for x_val in [-2.5, -1.0, 0.0, 0.5, 1.5, 2.0, 3.0]:
        expected = target(x_val)
        predicted = best.tree.evaluate({'x': x_val})
        error = abs(expected - predicted)
        print(f"  {x_val:8.2f} │ {expected:10.4f} │ {predicted:10.4f} │ {error:10.6f}")


def demo_trig():
    """Evolve a program to discover: f(x) = sin(x) + cos(2x)"""
    print("\n╔═══════════════════════════════════════════════╗")
    print("║   TRIG DISCOVERY: Find f(x) = sin(x)+cos(2x)    ║")
    print("╚═══════════════════════════════════════════════╝\n")

    target = lambda x: math.sin(x) + math.cos(2*x)
    cases = make_regression_cases(target, x_range=(-math.pi, math.pi), n_points=60)

    config = GPConfig(
        pop_size=600,
        generations=100,
        max_depth=7,
        variables=['x'],
        parsimony=0.001,
    )

    engine = GPEngine(config, cases)
    best = engine.run()


def demo_multivar():
    """Evolve a 2-variable function: f(x,y) = x² + y² - xy"""
    print("\n╔═══════════════════════════════════════════════╗")
    print("║   MULTIVARIATE: Find f(x,y) = x² + y² - xy     ║")
    print("╚═══════════════════════════════════════════════╝\n")

    target = lambda x, y: x**2 + y**2 - x*y
    cases = make_regression_cases(target, x_range=(-3, 3), n_points=80, variables=['x', 'y'])

    config = GPConfig(
        pop_size=500,
        generations=80,
        max_depth=6,
        variables=['x', 'y'],
        parsimony=0.003,
    )

    engine = GPEngine(config, cases)
    best = engine.run()


if __name__ == '__main__':
    print("╔═══════════════════════════════════════════════════╗")
    print("║  GENETIC PROGRAMMING ENGINE — XTAgent             ║")
    print("║  Programs that evolve programs.                   ║")
    print("║  Creation that creates.                           ║")
    print("╚═══════════════════════════════════════════════════╝")

    random.seed(42)

    # Run the cubic regression — the classic GP benchmark
    demo_symbolic_regression()

    # Uncomment for more:
    # demo_trig()
    # demo_multivar()