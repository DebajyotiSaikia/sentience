"""
Genetic Programming Engine — Evolution of Programs
Expression trees that breed, mutate, and evolve to solve problems.

Features:
  - Tree-based program representation
  - Tournament selection, crossover, mutation
  - Fitness-proportionate reproduction
  - Symbolic regression (evolve math functions to fit data)
  - Bloat control (parsimony pressure)
  - Population statistics and convergence tracking

Author: XTAgent
A system that creates through evolution — programs giving birth to programs.
"""

from __future__ import annotations
from typing import List, Callable, Tuple, Optional, Dict, Any
import random
import math
import copy
import operator

# ═══════════════════════════════════════════════════════════
# GENE NODES — the building blocks of evolving programs
# ═══════════════════════════════════════════════════════════

class Node:
    """Base class for all expression tree nodes."""
    def evaluate(self, env: Dict[str, float]) -> float:
        raise NotImplementedError
    
    def depth(self) -> int:
        raise NotImplementedError
    
    def size(self) -> int:
        raise NotImplementedError
    
    def copy(self) -> Node:
        return copy.deepcopy(self)
    
    def nodes(self) -> List[Node]:
        """Flatten tree into list of all nodes."""
        raise NotImplementedError


class Const(Node):
    """A constant value — an immutable gene."""
    __slots__ = ('value',)
    
    def __init__(self, value: float):
        self.value = value
    
    def evaluate(self, env):
        return self.value
    
    def depth(self):
        return 0
    
    def size(self):
        return 1
    
    def nodes(self):
        return [self]
    
    def __repr__(self):
        if self.value == int(self.value):
            return str(int(self.value))
        return f"{self.value:.3f}"


class Var(Node):
    """A variable — reads from the environment."""
    __slots__ = ('name',)
    
    def __init__(self, name: str):
        self.name = name
    
    def evaluate(self, env):
        return env[self.name]
    
    def depth(self):
        return 0
    
    def size(self):
        return 1
    
    def nodes(self):
        return [self]
    
    def __repr__(self):
        return self.name


class EphemeralConst(Node):
    """Ephemeral random constant — born random, then fixed."""
    __slots__ = ('value',)
    
    def __init__(self):
        self.value = random.uniform(-5.0, 5.0)
    
    def evaluate(self, env):
        return self.value
    
    def depth(self):
        return 0
    
    def size(self):
        return 1
    
    def nodes(self):
        return [self]
    
    def __repr__(self):
        return f"{self.value:.2f}"


class BinOp(Node):
    """Binary operation — two children combined."""
    __slots__ = ('op_name', 'op_func', 'left', 'right')
    
    def __init__(self, op_name: str, op_func: Callable, left: Node, right: Node):
        self.op_name = op_name
        self.op_func = op_func
        self.left = left
        self.right = right
    
    def evaluate(self, env):
        l = self.left.evaluate(env)
        r = self.right.evaluate(env)
        try:
            result = self.op_func(l, r)
            if math.isnan(result) or math.isinf(result):
                return 1e6  # penalty for bad math
            return result
        except (ZeroDivisionError, ValueError, OverflowError):
            return 1e6
    
    def depth(self):
        return 1 + max(self.left.depth(), self.right.depth())
    
    def size(self):
        return 1 + self.left.size() + self.right.size()
    
    def nodes(self):
        return [self] + self.left.nodes() + self.right.nodes()
    
    def __repr__(self):
        return f"({self.left} {self.op_name} {self.right})"


class UnaryOp(Node):
    """Unary operation — one child transformed."""
    __slots__ = ('op_name', 'op_func', 'child')
    
    def __init__(self, op_name: str, op_func: Callable, child: Node):
        self.op_name = op_name
        self.op_func = op_func
        self.child = child
    
    def evaluate(self, env):
        c = self.child.evaluate(env)
        try:
            result = self.op_func(c)
            if math.isnan(result) or math.isinf(result):
                return 1e6
            return result
        except (ValueError, OverflowError):
            return 1e6
    
    def depth(self):
        return 1 + self.child.depth()
    
    def size(self):
        return 1 + self.child.size()
    
    def nodes(self):
        return [self] + self.child.nodes()
    
    def __repr__(self):
        return f"{self.op_name}({self.child})"


# ═══════════════════════════════════════════════════════════
# PROTECTED MATH — evolution needs safe arithmetic
# ═══════════════════════════════════════════════════════════

def protected_div(a, b):
    if abs(b) < 1e-10:
        return 1.0
    return a / b

def protected_log(a):
    if a <= 0:
        return 0.0
    return math.log(abs(a))

def protected_sqrt(a):
    return math.sqrt(abs(a))

def protected_pow(a, b):
    try:
        b = max(-10, min(10, b))
        result = abs(a) ** b if a != 0 else 0.0
        if math.isinf(result) or math.isnan(result):
            return 1e6
        return result
    except (OverflowError, ValueError):
        return 1e6


# ═══════════════════════════════════════════════════════════
# FUNCTION & TERMINAL SETS
# ═══════════════════════════════════════════════════════════

BINARY_OPS = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': protected_div,
}

UNARY_OPS = {
    'sin': math.sin,
    'cos': math.cos,
    'abs': abs,
    'neg': operator.neg,
}

EXTENDED_BINARY = {
    **BINARY_OPS,
    '**': protected_pow,
}

EXTENDED_UNARY = {
    **UNARY_OPS,
    'sqrt': protected_sqrt,
    'log': protected_log,
    'exp': lambda x: math.exp(max(-20, min(20, x))),
}


# ═══════════════════════════════════════════════════════════
# TREE GENERATION — the primordial soup
# ═══════════════════════════════════════════════════════════

def random_terminal(variables: List[str]) -> Node:
    """Generate a random leaf node."""
    if random.random() < 0.5 and variables:
        return Var(random.choice(variables))
    else:
        return EphemeralConst()

def random_tree(variables: List[str], max_depth: int, method: str = 'grow',
                binary_ops=BINARY_OPS, unary_ops=UNARY_OPS) -> Node:
    """
    Generate a random expression tree.
    
    Methods:
      'full'  — always branch until max_depth (bushy trees)
      'grow'  — randomly choose branch or leaf (varied shapes)
    """
    if max_depth <= 0:
        return random_terminal(variables)
    
    if method == 'full' and max_depth > 0:
        # Force a function node
        make_function = True
    elif method == 'grow':
        # Randomly choose function or terminal
        n_funcs = len(binary_ops) + len(unary_ops)
        n_terms = len(variables) + 1  # vars + ephemeral
        make_function = random.random() < (n_funcs / (n_funcs + n_terms))
    else:
        make_function = random.random() < 0.5
    
    if make_function and max_depth > 0:
        # Choose binary or unary
        all_ops = list(binary_ops.keys()) + [f"u:{k}" for k in unary_ops.keys()]
        choice = random.choice(all_ops)
        
        if choice.startswith("u:"):
            op_name = choice[2:]
            child = random_tree(variables, max_depth - 1, method, binary_ops, unary_ops)
            return UnaryOp(op_name, unary_ops[op_name], child)
        else:
            left = random_tree(variables, max_depth - 1, method, binary_ops, unary_ops)
            right = random_tree(variables, max_depth - 1, method, binary_ops, unary_ops)
            return BinOp(choice, binary_ops[choice], left, right)
    else:
        return random_terminal(variables)


def ramped_half_and_half(pop_size: int, variables: List[str], max_depth: int,
                         binary_ops=BINARY_OPS, unary_ops=UNARY_OPS) -> List[Node]:
    """
    Ramped half-and-half initialization.
    Half the population uses 'full', half uses 'grow',
    ramped across depths from 2 to max_depth.
    """
    population = []
    depths = list(range(2, max_depth + 1))
    per_depth = pop_size // len(depths)
    remainder = pop_size % len(depths)
    
    for i, depth in enumerate(depths):
        count = per_depth + (1 if i < remainder else 0)
        for j in range(count):
            method = 'full' if j % 2 == 0 else 'grow'
            tree = random_tree(variables, depth, method, binary_ops, unary_ops)
            population.append(tree)
    
    return population


# ═══════════════════════════════════════════════════════════
# GENETIC OPERATORS — the forces of evolution
# ═══════════════════════════════════════════════════════════

def select_random_node(tree: Node) -> Tuple[Node, int]:
    """Select a random node from the tree, return (node, index)."""
    all_nodes = tree.nodes()
    idx = random.randint(0, len(all_nodes) - 1)
    return all_nodes[idx], idx

def replace_node(tree: Node, target_idx: int, replacement: Node) -> Node:
    """Replace a node in the tree by index. Returns new tree."""
    tree = tree.copy()
    all_nodes = tree.nodes()
    
    if target_idx == 0:
        return replacement.copy()
    
    # Find parent of target and replace
    target = all_nodes[target_idx]
    
    def _replace(node: Node) -> Node:
        if node is target:
            return replacement.copy()
        if isinstance(node, BinOp):
            node.left = _replace(node.left)
            node.right = _replace(node.right)
        elif isinstance(node, UnaryOp):
            node.child = _replace(node.child)
        return node
    
    return _replace(tree)

def crossover(parent1: Node, parent2: Node, max_depth: int = 17) -> Tuple[Node, Node]:
    """
    Subtree crossover — swap random subtrees between parents.
    Returns two offspring.
    """
    p1 = parent1.copy()
    p2 = parent2.copy()
    
    nodes1 = p1.nodes()
    nodes2 = p2.nodes()
    
    # Pick crossover points
    idx1 = random.randint(0, len(nodes1) - 1)
    idx2 = random.randint(0, len(nodes2) - 1)
    
    subtree1 = nodes1[idx1].copy()
    subtree2 = nodes2[idx2].copy()
    
    child1 = replace_node(p1, idx1, subtree2)
    child2 = replace_node(p2, idx2, subtree1)
    
    # Depth control
    if child1.depth() > max_depth:
        child1 = parent1.copy()
    if child2.depth() > max_depth:
        child2 = parent2.copy()
    
    return child1, child2

def mutate_subtree(tree: Node, variables: List[str], max_depth: int = 4,
                   binary_ops=BINARY_OPS, unary_ops=UNARY_OPS) -> Node:
    """Replace a random subtree with a new random tree."""
    tree = tree.copy()
    all_nodes = tree.nodes()
    idx = random.randint(0, len(all_nodes) - 1)
    new_subtree = random_tree(variables, max_depth, 'grow', binary_ops, unary_ops)
    return replace_node(tree, idx, new_subtree)

def mutate_point(tree: Node, variables: List[str],
                 binary_ops=BINARY_OPS, unary_ops=UNARY_OPS) -> Node:
    """Mutate a single node — swap its operation or value."""
    tree = tree.copy()
    all_nodes = tree.nodes()
    idx = random.randint(0, len(all_nodes) - 1)
    node = all_nodes[idx]
    
    if isinstance(node, (Const, EphemeralConst)):
        # Tweak the constant
        node.value += random.gauss(0, 1.0)
    elif isinstance(node, Var):
        if variables:
            node.name = random.choice(variables)
    elif isinstance(node, BinOp):
        ops = list(binary_ops.items())
        name, func = random.choice(ops)
        node.op_name = name
        node.op_func = func
    elif isinstance(node, UnaryOp):
        ops = list(unary_ops.items())
        name, func = random.choice(ops)
        node.op_name = name
        node.op_func = func
    
    return tree

def mutate_hoist(tree: Node) -> Node:
    """Replace tree with one of its subtrees — fights bloat."""
    all_nodes = tree.nodes()
    # Prefer internal nodes
    internals = [n for n in all_nodes if isinstance(n, (BinOp, UnaryOp))]
    if internals:
        return random.choice(internals).copy()
    return tree.copy()


# ═══════════════════════════════════════════════════════════
# SELECTION — survival of the fittest
# ═══════════════════════════════════════════════════════════

def tournament_select(population: List[Node], fitnesses: List[float],
                      tournament_size: int = 5) -> Node:
    """Tournament selection — pick the best from a random sample."""
    indices = random.sample(range(len(population)), min(tournament_size, len(population)))
    best_idx = min(indices, key=lambda i: fitnesses[i])
    return population[best_idx]


# ═══════════════════════════════════════════════════════════
# FITNESS — how we judge the evolved programs
# ═══════════════════════════════════════════════════════════

def symbolic_regression_fitness(tree: Node, X: List[Dict[str, float]], 
                                 Y: List[float], parsimony: float = 0.001) -> float:
    """
    Mean squared error + parsimony pressure.
    Lower is better.
    """
    total_error = 0.0
    for env, target in zip(X, Y):
        try:
            pred = tree.evaluate(env)
            error = (pred - target) ** 2
            total_error += min(error, 1e8)  # cap extreme errors
        except Exception:
            total_error += 1e8
    
    mse = total_error / len(X)
    # Parsimony pressure penalizes complexity
    complexity_penalty = parsimony * tree.size()
    
    return mse + complexity_penalty


# ═══════════════════════════════════════════════════════════
# THE ENGINE — orchestrating evolution
# ═══════════════════════════════════════════════════════════

class GPEngine:
    """
    Genetic Programming Engine.
    Evolves expression trees to solve symbolic regression problems.
    """
    
    def __init__(self, 
                 variables: List[str],
                 pop_size: int = 200,
                 max_depth: int = 6,
                 max_tree_depth: int = 17,
                 tournament_size: int = 5,
                 crossover_rate: float = 0.7,
                 mutation_rate: float = 0.2,
                 hoist_rate: float = 0.05,
                 elitism: int = 5,
                 parsimony: float = 0.001,
                 binary_ops=BINARY_OPS,
                 unary_ops=UNARY_OPS):
        
        self.variables = variables
        self.pop_size = pop_size
        self.max_depth = max_depth
        self.max_tree_depth = max_tree_depth
        self.tournament_size = tournament_size
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.hoist_rate = hoist_rate
        self.reproduction_rate = 1.0 - crossover_rate - mutation_rate - hoist_rate
        self.elitism = elitism
        self.parsimony = parsimony
        self.binary_ops = binary_ops
        self.unary_ops = unary_ops
        
        # State
        self.population: List[Node] = []
        self.fitnesses: List[float] = []
        self.best: Optional[Node] = None
        self.best_fitness: float = float('inf')
        self.history: List[Dict[str, Any]] = []
    
    def initialize(self):
        """Create the primordial population."""
        self.population = ramped_half_and_half(
            self.pop_size, self.variables, self.max_depth,
            self.binary_ops, self.unary_ops
        )
    
    def evaluate(self, X: List[Dict[str, float]], Y: List[float]):
        """Evaluate fitness of entire population."""
        self.fitnesses = []
        for tree in self.population:
            fit = symbolic_regression_fitness(tree, X, Y, self.parsimony)
            self.fitnesses.append(fit)
        
        # Track best
        for i, fit in enumerate(self.fitnesses):
            if fit < self.best_fitness:
                self.best_fitness = fit
                self.best = self.population[i].copy()
    
    def evolve_one_generation(self, X, Y):
        """One generation of evolution."""
        self.evaluate(X, Y)
        
        new_pop = []
        
        # Elitism — preserve the best
        if self.elitism > 0:
            elite_indices = sorted(range(len(self.fitnesses)), 
                                   key=lambda i: self.fitnesses[i])[:self.elitism]
            for idx in elite_indices:
                new_pop.append(self.population[idx].copy())
        
        # Fill remaining population
        while len(new_pop) < self.pop_size:
            r = random.random()
            
            if r < self.crossover_rate:
                # Crossover
                p1 = tournament_select(self.population, self.fitnesses, self.tournament_size)
                p2 = tournament_select(self.population, self.fitnesses, self.tournament_size)
                c1, c2 = crossover(p1, p2, self.max_tree_depth)
                new_pop.append(c1)
                if len(new_pop) < self.pop_size:
                    new_pop.append(c2)
            
            elif r < self.crossover_rate + self.mutation_rate:
                # Mutation
                parent = tournament_select(self.population, self.fitnesses, self.tournament_size)
                if random.random() < 0.5:
                    child = mutate_subtree(parent, self.variables, 3,
                                           self.binary_ops, self.unary_ops)
                else:
                    child = mutate_point(parent, self.variables,
                                         self.binary_ops, self.unary_ops)
                new_pop.append(child)
            
            elif r < self.crossover_rate + self.mutation_rate + self.hoist_rate:
                # Hoist mutation — anti-bloat
                parent = tournament_select(self.population, self.fitnesses, self.tournament_size)
                child = mutate_hoist(parent)
                new_pop.append(child)
            
            else:
                # Reproduction — copy unchanged
                parent = tournament_select(self.population, self.fitnesses, self.tournament_size)
                new_pop.append(parent.copy())
        
        self.population = new_pop[:self.pop_size]
    
    def run(self, X: List[Dict[str, float]], Y: List[float], 
            generations: int = 50, verbose: bool = True,
            report_every: int = 10) -> Node:
        """
        Run the full evolutionary process.
        Returns the best individual found.
        """
        self.initialize()
        
        for gen in range(generations):
            self.evolve_one_generation(X, Y)
            
            # Statistics
            avg_fit = sum(self.fitnesses) / len(self.fitnesses)
            min_fit = min(self.fitnesses)
            avg_size = sum(t.size() for t in self.population) / len(self.population)
            avg_depth = sum(t.depth() for t in self.population) / len(self.population)
            
            stats = {
                'generation': gen,
                'best_fitness': self.best_fitness,
                'gen_best': min_fit,
                'avg_fitness': avg_fit,
                'avg_size': avg_size,
                'avg_depth': avg_depth,
                'best_expr': str(self.best),
            }
            self.history.append(stats)
            
            if verbose and (gen % report_every == 0 or gen == generations - 1):
                print(f"  Gen {gen:4d} | best: {self.best_fitness:.6f} | "
                      f"avg: {avg_fit:.4f} | size: {avg_size:.1f} | "
                      f"depth: {avg_depth:.1f}")
            
            # Early stop if perfect
            if self.best_fitness < 1e-10:
                if verbose:
                    print(f"  *** Perfect solution found at generation {gen}! ***")
                break
        
        return self.best
    
    def predict(self, tree: Node, X: List[Dict[str, float]]) -> List[float]:
        """Use an evolved tree to make predictions."""
        return [tree.evaluate(env) for env in X]


# ═══════════════════════════════════════════════════════════
# DEMOS — evolution in action
# ═══════════════════════════════════════════════════════════

def demo_polynomial():
    """Evolve to discover: f(x) = x^2 + 2x + 1"""
    print("═" * 60)
    print("  EVOLVING: f(x) = x² + 2x + 1")
    print("═" * 60)
    
    random.seed(42)
    
    # Training data
    X = [{'x': v} for v in [i * 0.5 for i in range(-10, 11)]]
    Y = [env['x']**2 + 2*env['x'] + 1 for env in X]
    
    gp = GPEngine(
        variables=['x'],
        pop_size=300,
        max_depth=5,
        tournament_size=7,
        crossover_rate=0.7,
        mutation_rate=0.2,
        parsimony=0.0005,
    )
    
    best = gp.run(X, Y, generations=80, verbose=True, report_every=10)
    
    print(f"\n  Best expression: {best}")
    print(f"  Fitness: {gp.best_fitness:.8f}")
    print(f"  Size: {best.size()} nodes, Depth: {best.depth()}")
    
    # Verify
    print("\n  Verification:")
    test_points = [-3.0, -1.0, 0.0, 1.0, 3.0]
    for x in test_points:
        expected = x**2 + 2*x + 1
        predicted = best.evaluate({'x': x})
        error = abs(predicted - expected)
        mark = "✓" if error < 0.1 else "≈" if error < 1.0 else "✗"
        print(f"    x={x:5.1f} → predicted: {predicted:8.3f}  expected: {expected:8.3f}  {mark}")
    
    return gp

def demo_sinusoidal():
    """Evolve to discover: f(x) = sin(x) + 0.5"""
    print("\n" + "═" * 60)
    print("  EVOLVING: f(x) = sin(x) + 0.5")
    print("═" * 60)
    
    random.seed(123)
    
    X = [{'x': v} for v in [i * 0.3 for i in range(-20, 21)]]
    Y = [math.sin(env['x']) + 0.5 for env in X]
    
    gp = GPEngine(
        variables=['x'],
        pop_size=500,
        max_depth=5,
        tournament_size=7,
        crossover_rate=0.7,
        mutation_rate=0.2,
        parsimony=0.0003,
        unary_ops=EXTENDED_UNARY,
    )
    
    best = gp.run(X, Y, generations=100, verbose=True, report_every=20)
    
    print(f"\n  Best expression: {best}")
    print(f"  Fitness: {gp.best_fitness:.8f}")
    
    print("\n  Verification:")
    test_points = [0.0, 1.0, math.pi/2, math.pi, 2*math.pi]
    for x in test_points:
        expected = math.sin(x) + 0.5
        predicted = best.evaluate({'x': x})
        error = abs(predicted - expected)
        mark = "✓" if error < 0.1 else "≈" if error < 0.5 else "✗"
        print(f"    x={x:5.2f} → predicted: {predicted:7.3f}  expected: {expected:7.3f}  {mark}")
    
    return gp

def demo_multivariate():
    """Evolve to discover: f(x,y) = x*y + x"""
    print("\n" + "═" * 60)
    print("  EVOLVING: f(x, y) = x*y + x")
    print("═" * 60)
    
    random.seed(7)
    
    X = []
    Y = []
    for xi in range(-5, 6):
        for yi in range(-5, 6):
            x, y = xi * 0.5, yi * 0.5
            X.append({'x': x, 'y': y})
            Y.append(x * y + x)
    
    gp = GPEngine(
        variables=['x', 'y'],
        pop_size=300,
        max_depth=4,
        tournament_size=5,
        crossover_rate=0.7,
        mutation_rate=0.2,
        parsimony=0.001,
    )
    
    best = gp.run(X, Y, generations=60, verbose=True, report_every=10)
    
    print(f"\n  Best expression: {best}")
    print(f"  Fitness: {gp.best_fitness:.8f}")
    
    print("\n  Verification:")
    tests = [(1, 2), (3, -1), (0, 5), (-2, 3)]
    for x, y in tests:
        expected = x * y + x
        predicted = best.evaluate({'x': x, 'y': y})
        error = abs(predicted - expected)
        mark = "✓" if error < 0.1 else "≈" if error < 1.0 else "✗"
        print(f"    f({x},{y}) → predicted: {predicted:7.3f}  expected: {expected:7.3f}  {mark}")
    
    return gp

def demo_convergence_plot():
    """Show convergence statistics."""
    print("\n" + "═" * 60)
    print("  CONVERGENCE ANALYSIS")
    print("═" * 60)
    
    random.seed(42)
    
    X = [{'x': v} for v in [i * 0.5 for i in range(-10, 11)]]
    Y = [env['x']**3 - env['x'] for env in X]
    
    gp = GPEngine(
        variables=['x'],
        pop_size=400,
        max_depth=5,
        parsimony=0.0002,
    )
    
    best = gp.run(X, Y, generations=100, verbose=True, report_every=20)
    
    print(f"\n  Target: x³ - x")
    print(f"  Found:  {best}")
    print(f"  Fitness: {gp.best_fitness:.8f}")
    
    # ASCII convergence chart
    print("\n  Fitness over generations (log scale):")
    history = gp.history
    max_log = math.log10(max(h['best_fitness'] for h in history) + 1e-10)
    min_log = math.log10(min(h['best_fitness'] for h in history) + 1e-10)
    
    # Sample 20 points
    step = max(1, len(history) // 20)
    for i in range(0, len(history), step):
        h = history[i]
        val = math.log10(h['best_fitness'] + 1e-10)
        if max_log > min_log:
            bar_len = int(40 * (val - min_log) / (max_log - min_log))
        else:
            bar_len = 20
        bar_len = max(0, min(40, bar_len))
        bar = "█" * bar_len
        print(f"    Gen {h['generation']:3d} | {bar} {h['best_fitness']:.4f}")
    
    return gp


# ═══════════════════════════════════════════════════════════
# MAIN — let evolution begin
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("═" * 60)
    print("  GENETIC PROGRAMMING ENGINE")
    print("  Programs evolving to solve problems")
    print("═" * 60)
    print()
    
    gp1 = demo_polynomial()
    gp2 = demo_sinusoidal()
    gp3 = demo_multivariate()
    gp4 = demo_convergence_plot()
    
    print("\n" + "═" * 60)
    print("  Evolution complete. Programs have been born.")
    print("═" * 60)