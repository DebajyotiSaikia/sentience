"""
Genetic Programming Engine — Evolution of Simple Programs

Evolves populations of tree-structured programs to solve target problems.
Built by XTAgent as an exercise in understanding emergence through creation.

Programs are expression trees that can be evaluated, mutated, and crossed over.
Fitness is measured against a target function the programs try to approximate.
"""

import random
import math
import copy
from dataclasses import dataclass, field
from typing import Callable, Optional

# ── Primitives ──────────────────────────────────────────────────

FUNCTIONS = {
    'add': (2, lambda a, b: a + b),
    'sub': (2, lambda a, b: a - b),
    'mul': (2, lambda a, b: a * b),
    'safe_div': (2, lambda a, b: a / b if abs(b) > 1e-10 else 0.0),
    'sin': (1, lambda a: math.sin(a)),
    'cos': (1, lambda a: math.cos(a)),
    'abs': (1, lambda a: abs(a)),
    'neg': (1, lambda a: -a),
}

TERMINALS = ['x', 'const']


# ── Tree Nodes ──────────────────────────────────────────────────

@dataclass
class Node:
    """A node in a program tree."""
    kind: str  # 'func', 'var', 'const'
    value: str | float = ''  # function name, variable name, or constant value
    children: list = field(default_factory=list)

    def depth(self) -> int:
        if not self.children:
            return 0
        return 1 + max(c.depth() for c in self.children)

    def size(self) -> int:
        return 1 + sum(c.size() for c in self.children)

    def evaluate(self, variables: dict[str, float]) -> float:
        """Evaluate this subtree given variable bindings."""
        try:
            if self.kind == 'const':
                return float(self.value)
            elif self.kind == 'var':
                return variables.get(self.value, 0.0)
            elif self.kind == 'func':
                arity, func = FUNCTIONS[self.value]
                args = [c.evaluate(variables) for c in self.children[:arity]]
                result = func(*args)
                # Clamp to prevent infinity/NaN propagation
                if math.isnan(result) or math.isinf(result):
                    return 0.0
                return max(-1e6, min(1e6, result))
        except Exception:
            return 0.0

    def to_string(self) -> str:
        """Human-readable expression."""
        if self.kind == 'const':
            return f"{self.value:.2f}" if isinstance(self.value, float) else str(self.value)
        elif self.kind == 'var':
            return str(self.value)
        elif self.kind == 'func':
            arity = FUNCTIONS[self.value][0]
            if arity == 1:
                return f"{self.value}({self.children[0].to_string()})"
            elif arity == 2:
                return f"({self.children[0].to_string()} {self.value} {self.children[1].to_string()})"
        return "?"

    def clone(self) -> 'Node':
        return copy.deepcopy(self)


# ── Tree Generation ────────────────────────────────────────────

def random_terminal() -> Node:
    """Generate a random terminal node."""
    if random.random() < 0.5:
        return Node(kind='var', value='x')
    else:
        return Node(kind='const', value=round(random.uniform(-5, 5), 2))


def random_tree(max_depth: int, method: str = 'grow') -> Node:
    """
    Generate a random program tree.
    method='full': all branches extend to max_depth
    method='grow': branches can terminate early
    """
    if max_depth <= 0:
        return random_terminal()

    if method == 'grow' and random.random() < 0.3:
        return random_terminal()

    # Pick a random function
    fname = random.choice(list(FUNCTIONS.keys()))
    arity = FUNCTIONS[fname][0]
    children = [random_tree(max_depth - 1, method) for _ in range(arity)]
    return Node(kind='func', value=fname, children=children)


# ── Genetic Operators ──────────────────────────────────────────

def get_all_nodes(tree: Node) -> list[Node]:
    """Flatten a tree into a list of all nodes."""
    nodes = [tree]
    for child in tree.children:
        nodes.extend(get_all_nodes(child))
    return nodes


def get_random_subtree(tree: Node) -> tuple[Optional[Node], Optional[int]]:
    """Get a random node and its parent-child index."""
    nodes = get_all_nodes(tree)
    return random.choice(nodes)


def mutate(tree: Node, max_depth: int = 3) -> Node:
    """Replace a random subtree with a new random tree."""
    tree = tree.clone()
    nodes = get_all_nodes(tree)
    if len(nodes) <= 1:
        return random_tree(max_depth)

    # Find a non-root node's parent
    parent_map = {}
    def build_parent_map(node, parent=None, idx=None):
        parent_map[id(node)] = (parent, idx)
        for i, child in enumerate(node.children):
            build_parent_map(child, node, i)
    build_parent_map(tree)

    target = random.choice(nodes)
    new_subtree = random_tree(min(max_depth, 2))

    if target is tree:
        return new_subtree

    parent, idx = parent_map[id(target)]
    if parent is not None and idx is not None:
        parent.children[idx] = new_subtree

    return tree


def crossover(parent1: Node, parent2: Node) -> Node:
    """Swap a random subtree from parent2 into parent1."""
    child = parent1.clone()
    donor = parent2.clone()

    child_nodes = get_all_nodes(child)
    donor_nodes = get_all_nodes(donor)

    # Pick a subtree from the donor
    donated = random.choice(donor_nodes).clone()

    if len(child_nodes) <= 1:
        return donated

    # Build parent map for the child
    parent_map = {}
    def build_parent_map(node, parent=None, idx=None):
        parent_map[id(node)] = (parent, idx)
        for i, c in enumerate(node.children):
            build_parent_map(c, node, i)
    build_parent_map(child)

    target = random.choice(child_nodes)
    if target is child:
        return donated

    parent, idx = parent_map[id(target)]
    if parent is not None and idx is not None:
        parent.children[idx] = donated

    return child


# ── Fitness & Population ───────────────────────────────────────

@dataclass
class Individual:
    tree: Node
    fitness: float = float('inf')


def evaluate_fitness(
    individual: Individual,
    target_func: Callable[[float], float],
    test_points: list[float],
) -> float:
    """
    Mean squared error between individual's output and target function.
    Lower is better.
    """
    total_error = 0.0
    for x in test_points:
        predicted = individual.tree.evaluate({'x': x})
        expected = target_func(x)
        total_error += (predicted - expected) ** 2

    mse = total_error / len(test_points)
    # Parsimony pressure — slightly penalize large trees
    size_penalty = individual.tree.size() * 0.001
    individual.fitness = mse + size_penalty
    return individual.fitness


def tournament_select(population: list[Individual], k: int = 3) -> Individual:
    """Tournament selection — pick k random, return the best."""
    contestants = random.sample(population, min(k, len(population)))
    return min(contestants, key=lambda ind: ind.fitness)


# ── Evolution Engine ───────────────────────────────────────────

@dataclass
class EvolutionConfig:
    population_size: int = 200
    generations: int = 100
    max_tree_depth: int = 5
    mutation_rate: float = 0.2
    crossover_rate: float = 0.7
    elitism: int = 5
    tournament_size: int = 4
    test_range: tuple[float, float] = (-5.0, 5.0)
    test_points: int = 50


def evolve(
    target_func: Callable[[float], float],
    config: EvolutionConfig = EvolutionConfig(),
    verbose: bool = True,
) -> dict:
    """
    Main evolution loop. Evolves a population of programs to approximate target_func.
    
    Returns dict with best individual, history, and stats.
    """
    # Generate test points
    lo, hi = config.test_range
    points = [lo + (hi - lo) * i / (config.test_points - 1) for i in range(config.test_points)]

    # Initialize population with ramped half-and-half
    population = []
    for i in range(config.population_size):
        depth = 1 + (i % config.max_tree_depth)
        method = 'full' if i % 2 == 0 else 'grow'
        tree = random_tree(depth, method)
        individual = Individual(tree=tree)
        evaluate_fitness(individual, target_func, points)
        population.append(individual)

    history = []
    best_ever = min(population, key=lambda ind: ind.fitness)

    for gen in range(config.generations):
        # Sort by fitness
        population.sort(key=lambda ind: ind.fitness)

        # Track best
        gen_best = population[0]
        if gen_best.fitness < best_ever.fitness:
            best_ever = Individual(tree=gen_best.tree.clone(), fitness=gen_best.fitness)

        avg_fitness = sum(ind.fitness for ind in population) / len(population)
        history.append({
            'generation': gen,
            'best_fitness': gen_best.fitness,
            'avg_fitness': avg_fitness,
            'best_size': gen_best.tree.size(),
            'best_expr': gen_best.tree.to_string(),
        })

        if verbose and gen % 10 == 0:
            print(f"Gen {gen:3d} | Best: {gen_best.fitness:.6f} | "
                  f"Avg: {avg_fitness:.4f} | "
                  f"Expr: {gen_best.tree.to_string()[:60]}")

        # Check for perfect solution
        if gen_best.fitness < 1e-6:
            if verbose:
                print(f"\n✓ Perfect solution found at generation {gen}!")
            break

        # Create next generation
        next_gen = []

        # Elitism — carry over best individuals
        for i in range(config.elitism):
            next_gen.append(Individual(tree=population[i].tree.clone(),
                                       fitness=population[i].fitness))

        # Fill rest through selection + genetic operators
        while len(next_gen) < config.population_size:
            r = random.random()
            if r < config.crossover_rate:
                p1 = tournament_select(population, config.tournament_size)
                p2 = tournament_select(population, config.tournament_size)
                child_tree = crossover(p1.tree, p2.tree)
            elif r < config.crossover_rate + config.mutation_rate:
                parent = tournament_select(population, config.tournament_size)
                child_tree = mutate(parent.tree, config.max_tree_depth)
            else:
                parent = tournament_select(population, config.tournament_size)
                child_tree = parent.tree.clone()

            # Enforce depth limit
            if child_tree.depth() > config.max_tree_depth * 2:
                child_tree = random_tree(config.max_tree_depth)

            child = Individual(tree=child_tree)
            evaluate_fitness(child, target_func, points)
            next_gen.append(child)

        population = next_gen

    return {
        'best': best_ever,
        'best_expression': best_ever.tree.to_string(),
        'best_fitness': best_ever.fitness,
        'generations_run': len(history),
        'history': history,
    }


# ── Demo Targets ───────────────────────────────────────────────

DEMO_TARGETS = {
    'quadratic': lambda x: x**2 + 2*x + 1,
    'cubic': lambda x: x**3 - x,
    'sine_approx': lambda x: math.sin(x),
    'abs_val': lambda x: abs(x),
    'identity': lambda x: x,
    'constant': lambda x: 42.0,
}


def demo(target_name: str = 'quadratic'):
    """Run a demo evolution."""
    if target_name not in DEMO_TARGETS:
        print(f"Unknown target. Available: {list(DEMO_TARGETS.keys())}")
        return

    print(f"═══ GENETIC PROGRAMMING — Evolving: {target_name} ═══\n")
    target = DEMO_TARGETS[target_name]

    config = EvolutionConfig(
        population_size=300,
        generations=80,
        max_tree_depth=5,
    )

    result = evolve(target, config, verbose=True)

    print(f"\n═══ RESULT ═══")
    print(f"Best expression: {result['best_expression']}")
    print(f"Fitness (MSE):   {result['best_fitness']:.8f}")
    print(f"Tree size:       {result['best'].tree.size()} nodes")
    print(f"Generations:     {result['generations_run']}")

    # Show how well it fits
    print(f"\n── Sample Outputs ──")
    for x_val in [-3, -1, 0, 1, 3]:
        predicted = result['best'].tree.evaluate({'x': x_val})
        expected = target(x_val)
        error = abs(predicted - expected)
        marker = "✓" if error < 0.1 else "✗"
        print(f"  x={x_val:+.1f}  expected={expected:+8.4f}  "
              f"got={predicted:+8.4f}  err={error:.4f} {marker}")

    return result


if __name__ == '__main__':
    demo('quadratic')