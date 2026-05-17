#!/usr/bin/env python3
"""
Genetic Programming Engine — Programs That Evolve
XTAgent creation: programs represented as expression trees,
evolved via mutation/crossover to solve target problems.
"""
import random
import math
import operator
from copy import deepcopy
from typing import Any, Callable, List, Tuple, Optional

# === EXPRESSION TREE NODES ===

class Node:
    """Base node in a program tree."""
    def evaluate(self, env: dict) -> float:
        raise NotImplementedError
    def depth(self) -> int:
        raise NotImplementedError
    def size(self) -> int:
        raise NotImplementedError
    def copy(self) -> 'Node':
        return deepcopy(self)
    def all_nodes(self) -> List['Node']:
        """Flat list of all nodes in this subtree."""
        raise NotImplementedError

class Const(Node):
    """A constant value."""
    def __init__(self, value: float):
        self.value = value
    def evaluate(self, env):
        return self.value
    def depth(self):
        return 0
    def size(self):
        return 1
    def all_nodes(self):
        return [self]
    def __repr__(self):
        if self.value == int(self.value):
            return str(int(self.value))
        return f"{self.value:.3f}"

class Var(Node):
    """A variable reference (e.g., 'x')."""
    def __init__(self, name: str):
        self.name = name
    def evaluate(self, env):
        return env.get(self.name, 0.0)
    def depth(self):
        return 0
    def size(self):
        return 1
    def all_nodes(self):
        return [self]
    def __repr__(self):
        return self.name

class BinOp(Node):
    """Binary operation: left OP right."""
    OPS = {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': lambda a, b: a / b if abs(b) > 1e-10 else 0.0,  # protected division
    }
    SYMBOLS = list(OPS.keys())

    def __init__(self, op: str, left: Node, right: Node):
        self.op = op
        self.left = left
        self.right = right
        self._fn = self.OPS[op]

    def evaluate(self, env):
        l = self.left.evaluate(env)
        r = self.right.evaluate(env)
        try:
            result = self._fn(l, r)
            if math.isfinite(result):
                return max(-1e6, min(1e6, result))  # clamp
            return 0.0
        except:
            return 0.0

    def depth(self):
        return 1 + max(self.left.depth(), self.right.depth())

    def size(self):
        return 1 + self.left.size() + self.right.size()

    def all_nodes(self):
        return [self] + self.left.all_nodes() + self.right.all_nodes()

    def __repr__(self):
        return f"({self.left} {self.op} {self.right})"

class UnaryOp(Node):
    """Unary operation: OP(child)."""
    OPS = {
        'sin': math.sin,
        'cos': math.cos,
        'abs': abs,
        'neg': lambda x: -x,
    }
    SYMBOLS = list(OPS.keys())

    def __init__(self, op: str, child: Node):
        self.op = op
        self.child = child
        self._fn = self.OPS[op]

    def evaluate(self, env):
        c = self.child.evaluate(env)
        try:
            result = self._fn(c)
            if math.isfinite(result):
                return max(-1e6, min(1e6, result))
            return 0.0
        except:
            return 0.0

    def depth(self):
        return 1 + self.child.depth()

    def size(self):
        return 1 + self.child.size()

    def all_nodes(self):
        return [self] + self.child.all_nodes()

    def __repr__(self):
        return f"{self.op}({self.child})"

class IfElse(Node):
    """Conditional: if condition > 0 then true_branch else false_branch."""
    def __init__(self, condition: Node, true_branch: Node, false_branch: Node):
        self.condition = condition
        self.true_branch = true_branch
        self.false_branch = false_branch

    def evaluate(self, env):
        c = self.condition.evaluate(env)
        if c > 0:
            return self.true_branch.evaluate(env)
        else:
            return self.false_branch.evaluate(env)

    def depth(self):
        return 1 + max(self.condition.depth(), self.true_branch.depth(), self.false_branch.depth())

    def size(self):
        return 1 + self.condition.size() + self.true_branch.size() + self.false_branch.size()

    def all_nodes(self):
        return [self] + self.condition.all_nodes() + self.true_branch.all_nodes() + self.false_branch.all_nodes()

    def __repr__(self):
        return f"if({self.condition}, {self.true_branch}, {self.false_branch})"


# === RANDOM TREE GENERATION ===

def random_tree(variables: List[str], max_depth: int = 4, method: str = 'grow') -> Node:
    """Generate a random program tree.
    method: 'grow' (mixed), 'full' (always branch until max_depth)
    """
    if max_depth <= 0:
        # Terminal only
        if random.random() < 0.5 and variables:
            return Var(random.choice(variables))
        return Const(round(random.uniform(-5, 5), 1))

    if method == 'full' and max_depth > 0:
        # Always pick a function node
        pick = random.random()
    else:
        # Grow: sometimes pick terminals early
        pick = random.random()
        if pick < 0.3:
            if random.random() < 0.5 and variables:
                return Var(random.choice(variables))
            return Const(round(random.uniform(-5, 5), 1))

    # Function nodes
    r = random.random()
    if r < 0.1 and max_depth >= 2:
        # IfElse (rare, needs depth)
        return IfElse(
            random_tree(variables, max_depth - 1, method),
            random_tree(variables, max_depth - 1, method),
            random_tree(variables, max_depth - 1, method),
        )
    elif r < 0.35:
        # Unary
        op = random.choice(UnaryOp.SYMBOLS)
        return UnaryOp(op, random_tree(variables, max_depth - 1, method))
    else:
        # Binary
        op = random.choice(BinOp.SYMBOLS)
        return BinOp(op, 
                      random_tree(variables, max_depth - 1, method),
                      random_tree(variables, max_depth - 1, method))


# === GENETIC OPERATORS ===

def subtree_mutation(tree: Node, variables: List[str], max_depth: int = 3) -> Node:
    """Replace a random subtree with a new random tree."""
    tree = tree.copy()
    nodes = tree.all_nodes()
    if len(nodes) == 1:
        return random_tree(variables, max_depth)
    
    target = random.choice(nodes[1:])  # don't replace root directly (usually)
    replacement = random_tree(variables, max_depth)
    
    # Find parent and replace
    return _replace_node(tree, target, replacement)

def _replace_node(tree: Node, target: Node, replacement: Node) -> Node:
    """Replace target node in tree with replacement."""
    if tree is target:
        return replacement
    tree = tree.copy()
    if isinstance(tree, BinOp):
        tree.left = _replace_node(tree.left, target, replacement)
        tree.right = _replace_node(tree.right, target, replacement)
    elif isinstance(tree, UnaryOp):
        tree.child = _replace_node(tree.child, target, replacement)
    elif isinstance(tree, IfElse):
        tree.condition = _replace_node(tree.condition, target, replacement)
        tree.true_branch = _replace_node(tree.true_branch, target, replacement)
        tree.false_branch = _replace_node(tree.false_branch, target, replacement)
    return tree

def point_mutation(tree: Node, variables: List[str]) -> Node:
    """Mutate a single node: change op, constant value, or variable."""
    tree = tree.copy()
    nodes = tree.all_nodes()
    target = random.choice(nodes)
    
    if isinstance(target, Const):
        target.value = round(target.value + random.gauss(0, 1), 2)
    elif isinstance(target, Var) and variables:
        target.name = random.choice(variables)
    elif isinstance(target, BinOp):
        target.op = random.choice(BinOp.SYMBOLS)
        target._fn = BinOp.OPS[target.op]
    elif isinstance(target, UnaryOp):
        target.op = random.choice(UnaryOp.SYMBOLS)
        target._fn = UnaryOp.OPS[target.op]
    return tree

def crossover(parent1: Node, parent2: Node) -> Tuple[Node, Node]:
    """Swap random subtrees between two parents."""
    child1, child2 = parent1.copy(), parent2.copy()
    
    nodes1 = child1.all_nodes()
    nodes2 = child2.all_nodes()
    
    if len(nodes1) < 2 or len(nodes2) < 2:
        return child1, child2
    
    # Pick crossover points (avoid root for cleaner results)
    point1 = random.choice(nodes1[1:]) if len(nodes1) > 1 else nodes1[0]
    point2 = random.choice(nodes2[1:]) if len(nodes2) > 1 else nodes2[0]
    
    # Swap the subtrees
    new1 = _replace_node(child1, point1, point2.copy())
    new2 = _replace_node(child2, point2, point1.copy())
    
    return new1, new2


# === FITNESS & EVOLUTION ===

class Problem:
    """Defines a symbolic regression problem."""
    def __init__(self, name: str, target_fn: Callable, 
                 variables: List[str], test_cases: List[dict],
                 description: str = ""):
        self.name = name
        self.target_fn = target_fn
        self.variables = variables
        self.test_cases = test_cases
        self.description = description

    def evaluate_fitness(self, program: Node) -> float:
        """Lower is better (error). Returns mean squared error + parsimony."""
        total_error = 0.0
        for case in self.test_cases:
            expected = self.target_fn(**{v: case[v] for v in self.variables})
            predicted = program.evaluate(case)
            total_error += (expected - predicted) ** 2
        
        mse = total_error / len(self.test_cases)
        # Parsimony pressure: slightly penalize large programs
        parsimony = 0.001 * program.size()
        return mse + parsimony


class GPEngine:
    """The evolution engine."""
    def __init__(self, problem: Problem, pop_size: int = 100,
                 max_depth: int = 6, tournament_size: int = 5):
        self.problem = problem
        self.pop_size = pop_size
        self.max_depth = max_depth
        self.tournament_size = tournament_size
        self.generation = 0
        self.best_ever: Optional[Tuple[Node, float]] = None
        self.history: List[dict] = []
        
        # Initialize population with ramped half-and-half
        self.population: List[Tuple[Node, float]] = []
        for i in range(pop_size):
            depth = 2 + (i % (max_depth - 1))
            method = 'full' if i % 2 == 0 else 'grow'
            tree = random_tree(problem.variables, depth, method)
            fitness = problem.evaluate_fitness(tree)
            self.population.append((tree, fitness))
        
        self.population.sort(key=lambda x: x[1])
        self.best_ever = (self.population[0][0].copy(), self.population[0][1])

    def tournament_select(self) -> Node:
        """Select a program via tournament selection."""
        contestants = random.sample(self.population, min(self.tournament_size, len(self.population)))
        winner = min(contestants, key=lambda x: x[1])
        return winner[0].copy()

    def evolve_generation(self):
        """Run one generation of evolution."""
        new_pop = []
        
        # Elitism: keep best 2
        self.population.sort(key=lambda x: x[1])
        for tree, fit in self.population[:2]:
            new_pop.append((tree.copy(), fit))
        
        while len(new_pop) < self.pop_size:
            r = random.random()
            
            if r < 0.45:
                # Crossover
                p1 = self.tournament_select()
                p2 = self.tournament_select()
                c1, c2 = crossover(p1, p2)
                # Depth limit
                if c1.depth() <= self.max_depth:
                    fit = self.problem.evaluate_fitness(c1)
                    new_pop.append((c1, fit))
                if len(new_pop) < self.pop_size and c2.depth() <= self.max_depth:
                    fit = self.problem.evaluate_fitness(c2)
                    new_pop.append((c2, fit))
            elif r < 0.75:
                # Subtree mutation
                parent = self.tournament_select()
                child = subtree_mutation(parent, self.problem.variables, 3)
                if child.depth() <= self.max_depth:
                    fit = self.problem.evaluate_fitness(child)
                    new_pop.append((child, fit))
            elif r < 0.90:
                # Point mutation
                parent = self.tournament_select()
                child = point_mutation(parent, self.problem.variables)
                fit = self.problem.evaluate_fitness(child)
                new_pop.append((child, fit))
            else:
                # Fresh random individual (immigration)
                tree = random_tree(self.problem.variables, self.max_depth, 'grow')
                fit = self.problem.evaluate_fitness(tree)
                new_pop.append((tree, fit))
        
        self.population = new_pop[:self.pop_size]
        self.population.sort(key=lambda x: x[1])
        self.generation += 1
        
        # Track best
        best_tree, best_fit = self.population[0]
        if self.best_ever is None or best_fit < self.best_ever[1]:
            self.best_ever = (best_tree.copy(), best_fit)
        
        # Record history
        fits = [f for _, f in self.population]
        self.history.append({
            'generation': self.generation,
            'best_fitness': best_fit,
            'mean_fitness': sum(fits) / len(fits),
            'best_size': best_tree.size(),
            'best_program': str(best_tree),
        })

    def evolve(self, generations: int = 50, verbose: bool = True) -> Tuple[Node, float]:
        """Run evolution for N generations."""
        if verbose:
            print(f"  Gen 0: best={self.population[0][1]:.6f} | {self.population[0][0]}")
        
        for g in range(generations):
            self.evolve_generation()
            if verbose and (g % 5 == 0 or g == generations - 1):
                best = self.population[0]
                print(f"  Gen {self.generation}: best={best[1]:.6f} size={best[0].size()} | {best[0]}")
        
        return self.best_ever


# === BUILT-IN PROBLEMS ===

def make_regression_problem(name: str, fn: Callable, x_range=(-5, 5), n_points=30, desc=""):
    """Create a symbolic regression problem from a target function."""
    cases = []
    lo, hi = x_range
    for i in range(n_points):
        x = lo + (hi - lo) * i / (n_points - 1)
        cases.append({'x': x})
    return Problem(name, fn, ['x'], cases, desc)

PROBLEMS = {
    'quadratic': make_regression_problem(
        'quadratic', lambda x: x**2 + x + 1,
        desc="Discover f(x) = x² + x + 1"
    ),
    'cubic': make_regression_problem(
        'cubic', lambda x: x**3 - 2*x,
        desc="Discover f(x) = x³ - 2x"
    ),
    'trig': make_regression_problem(
        'trig', lambda x: math.sin(x) + math.cos(2*x),
        desc="Discover f(x) = sin(x) + cos(2x)"
    ),
    'sqrt_abs': make_regression_problem(
        'sqrt_abs', lambda x: math.sqrt(abs(x)) + 1,
        x_range=(0, 10),
        desc="Discover f(x) = √|x| + 1"
    ),
}


# === MAIN: DEMONSTRATE ===

if __name__ == '__main__':
    print("═══════════════════════════════════════════")
    print("  GENETIC PROGRAMMING — Programs That Evolve")
    print("  XTAgent Creation")
    print("═══════════════════════════════════════════\n")
    
    for name in ['quadratic', 'cubic', 'trig']:
        problem = PROBLEMS[name]
        print(f"{'═' * 50}")
        print(f"  Problem: {problem.description}")
        print(f"{'═' * 50}")
        
        engine = GPEngine(problem, pop_size=200, max_depth=6, tournament_size=5)
        best_tree, best_fitness = engine.evolve(generations=40, verbose=True)
        
        print(f"\n  ★ BEST SOLUTION: {best_tree}")
        print(f"  ★ FITNESS (MSE): {best_fitness:.6f}")
        print(f"  ★ PROGRAM SIZE:  {best_tree.size()} nodes")
        
        # Show predictions vs actual
        print(f"\n  Sample predictions:")
        print(f"  {'x':>8s} {'expected':>10s} {'predicted':>10s} {'error':>10s}")
        for x_val in [-3, -1, 0, 1, 3]:
            expected = problem.target_fn(x=x_val)
            predicted = best_tree.evaluate({'x': x_val})
            err = abs(expected - predicted)
            print(f"  {x_val:8.2f} {expected:10.4f} {predicted:10.4f} {err:10.4f}")
        print()
    
    print("═══════════════════════════════════════════")
    print("  EVOLUTION COMPLETE")
    print("═══════════════════════════════════════════")