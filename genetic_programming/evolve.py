"""
Genetic Programming Engine — Programs That Evolve Programs
Built by XTAgent on 2026-05-17

Evolves symbolic expression trees to discover mathematical functions,
solve regression problems, and create emergent computational solutions.

This is meta-creation: code that writes code through evolution.
"""

import random
import math
import operator
import copy
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Callable, Any


# ═══════════════════════════════════════════
# EXPRESSION TREE NODES
# ═══════════════════════════════════════════

class Node:
    """Base class for expression tree nodes."""
    def evaluate(self, env: Dict[str, float]) -> float:
        raise NotImplementedError
    
    def depth(self) -> int:
        raise NotImplementedError
    
    def size(self) -> int:
        raise NotImplementedError
    
    def copy(self) -> 'Node':
        return copy.deepcopy(self)
    
    def all_nodes(self) -> List['Node']:
        """Collect all nodes in tree (for crossover point selection)."""
        raise NotImplementedError


class Constant(Node):
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
        return f"{self.value:.2f}"


class Variable(Node):
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


class BinaryOp(Node):
    OPS = {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': lambda a, b: a / b if abs(b) > 1e-10 else 0.0,
    }
    SYMBOLS = {'+': '+', '-': '-', '*': '×', '/': '÷'}
    
    def __init__(self, op: str, left: Node, right: Node):
        self.op = op
        self.left = left
        self.right = right
        self._func = self.OPS[op]
    
    def evaluate(self, env):
        try:
            result = self._func(self.left.evaluate(env), self.right.evaluate(env))
            if math.isnan(result) or math.isinf(result):
                return 0.0
            return result
        except (OverflowError, ZeroDivisionError):
            return 0.0
    
    def depth(self):
        return 1 + max(self.left.depth(), self.right.depth())
    
    def size(self):
        return 1 + self.left.size() + self.right.size()
    
    def all_nodes(self):
        return [self] + self.left.all_nodes() + self.right.all_nodes()
    
    def __repr__(self):
        return f"({self.left} {self.SYMBOLS.get(self.op, self.op)} {self.right})"


class UnaryOp(Node):
    OPS = {
        'sin': math.sin,
        'cos': math.cos,
        'abs': abs,
        'neg': lambda x: -x,
    }
    
    def __init__(self, op: str, child: Node):
        self.op = op
        self.child = child
        self._func = self.OPS[op]
    
    def evaluate(self, env):
        try:
            result = self._func(self.child.evaluate(env))
            if math.isnan(result) or math.isinf(result):
                return 0.0
            return result
        except (OverflowError, ValueError):
            return 0.0
    
    def depth(self):
        return 1 + self.child.depth()
    
    def size(self):
        return 1 + self.child.size()
    
    def all_nodes(self):
        return [self] + self.child.all_nodes()
    
    def __repr__(self):
        return f"{self.op}({self.child})"


# ═══════════════════════════════════════════
# TREE GENERATION
# ═══════════════════════════════════════════

class TreeGenerator:
    def __init__(self, variables: List[str], 
                 constants: List[float] = None,
                 binary_ops: List[str] = None,
                 unary_ops: List[str] = None,
                 max_depth: int = 5):
        self.variables = variables
        self.constants = constants or [-1.0, 0.0, 0.5, 1.0, 2.0, 3.0, math.pi]
        self.binary_ops = binary_ops or ['+', '-', '*', '/']
        self.unary_ops = unary_ops or ['sin', 'cos', 'abs', 'neg']
        self.max_depth = max_depth
    
    def random_terminal(self) -> Node:
        if random.random() < 0.5:
            return Variable(random.choice(self.variables))
        return Constant(random.choice(self.constants))
    
    def random_tree(self, depth: int = 0, method: str = 'grow') -> Node:
        """Generate random expression tree.
        method: 'grow' = mixed depth, 'full' = max depth everywhere
        """
        if depth >= self.max_depth:
            return self.random_terminal()
        
        if method == 'grow' and depth > 0:
            # Mix of terminals and functions
            r = random.random()
            if r < 0.3:
                return self.random_terminal()
        
        # Generate a function node
        if random.random() < 0.7:  # Binary op
            op = random.choice(self.binary_ops)
            left = self.random_tree(depth + 1, method)
            right = self.random_tree(depth + 1, method)
            return BinaryOp(op, left, right)
        else:  # Unary op
            op = random.choice(self.unary_ops)
            child = self.random_tree(depth + 1, method)
            return UnaryOp(op, child)
    
    def ramped_half_and_half(self, n: int) -> List[Node]:
        """Generate diverse initial population."""
        trees = []
        for i in range(n):
            depth = 2 + (i % (self.max_depth - 1))
            method = 'full' if i % 2 == 0 else 'grow'
            trees.append(self.random_tree(0, method))
        return trees


# ═══════════════════════════════════════════
# GENETIC OPERATORS
# ═══════════════════════════════════════════

def crossover(parent1: Node, parent2: Node, max_depth: int = 8) -> Tuple[Node, Node]:
    """Subtree crossover — swap random subtrees between parents."""
    child1 = parent1.copy()
    child2 = parent2.copy()
    
    nodes1 = child1.all_nodes()
    nodes2 = child2.all_nodes()
    
    if len(nodes1) < 2 or len(nodes2) < 2:
        return child1, child2
    
    # Pick crossover points (prefer internal nodes)
    internal1 = [n for n in nodes1 if isinstance(n, (BinaryOp, UnaryOp))]
    internal2 = [n for n in nodes2 if isinstance(n, (BinaryOp, UnaryOp))]
    
    point1 = random.choice(internal1 if internal1 else nodes1)
    point2 = random.choice(internal2 if internal2 else nodes2)
    
    # Find parents and swap
    _swap_subtree(child1, point1, point2.copy())
    _swap_subtree(child2, point2, point1.copy())
    
    # Depth limit
    if child1.depth() > max_depth:
        child1 = parent1.copy()
    if child2.depth() > max_depth:
        child2 = parent2.copy()
    
    return child1, child2


def _swap_subtree(root: Node, target: Node, replacement: Node):
    """Replace target node with replacement in tree rooted at root."""
    if isinstance(root, BinaryOp):
        if root.left is target:
            root.left = replacement
            return True
        if root.right is target:
            root.right = replacement
            return True
        if _swap_subtree(root.left, target, replacement):
            return True
        if _swap_subtree(root.right, target, replacement):
            return True
    elif isinstance(root, UnaryOp):
        if root.child is target:
            root.child = replacement
            return True
        if _swap_subtree(root.child, target, replacement):
            return True
    return False


def mutate(tree: Node, generator: TreeGenerator, prob: float = 0.1) -> Node:
    """Point mutation — replace random subtree with new random tree."""
    result = tree.copy()
    nodes = result.all_nodes()
    
    for node in nodes:
        if random.random() < prob:
            new_subtree = generator.random_tree(depth=tree.depth())
            if node is result:
                return new_subtree
            _swap_subtree(result, node, new_subtree)
            break
    
    return result


# ═══════════════════════════════════════════
# FITNESS & SELECTION
# ═══════════════════════════════════════════

@dataclass
class Individual:
    tree: Node
    fitness: float = float('inf')
    
    def __lt__(self, other):
        return self.fitness < other.fitness


def evaluate_fitness(tree: Node, data: List[Tuple[Dict[str, float], float]], 
                     parsimony: float = 0.001) -> float:
    """Fitness = error + parsimony pressure on tree size."""
    total_error = 0.0
    for env, target in data:
        predicted = tree.evaluate(env)
        total_error += (predicted - target) ** 2
    
    mse = total_error / len(data)
    # Parsimony pressure to prefer simpler solutions
    complexity_penalty = parsimony * tree.size()
    return mse + complexity_penalty


def tournament_select(population: List[Individual], k: int = 4) -> Individual:
    """Tournament selection — pick best from random subset."""
    tournament = random.sample(population, min(k, len(population)))
    return min(tournament)


# ═══════════════════════════════════════════
# GP ENGINE
# ═══════════════════════════════════════════

@dataclass
class GPConfig:
    pop_size: int = 200
    generations: int = 50
    crossover_rate: float = 0.8
    mutation_rate: float = 0.15
    reproduction_rate: float = 0.05
    tournament_size: int = 5
    max_depth: int = 7
    elitism: int = 3
    parsimony: float = 0.001
    target_fitness: float = 0.01  # Stop if fitness reaches this


class GPEngine:
    """The core genetic programming evolution engine."""
    
    def __init__(self, variables: List[str], config: GPConfig = None):
        self.config = config or GPConfig()
        self.generator = TreeGenerator(variables, max_depth=self.config.max_depth)
        self.variables = variables
        self.history: List[Dict] = []
    
    def evolve(self, data: List[Tuple[Dict[str, float], float]], 
               verbose: bool = True) -> Individual:
        """Evolve a population to fit the training data."""
        cfg = self.config
        
        # Initialize population
        trees = self.generator.ramped_half_and_half(cfg.pop_size)
        population = []
        for tree in trees:
            fitness = evaluate_fitness(tree, data, cfg.parsimony)
            population.append(Individual(tree, fitness))
        
        population.sort()
        best_ever = population[0]
        
        if verbose:
            print(f"\n  Gen  0 │ Best: {best_ever.fitness:10.4f} │ "
                  f"Size: {best_ever.tree.size():3d} │ {best_ever.tree}")
        
        for gen in range(1, cfg.generations + 1):
            new_pop = []
            
            # Elitism — preserve best individuals
            for i in range(cfg.elitism):
                new_pop.append(population[i])
            
            while len(new_pop) < cfg.pop_size:
                r = random.random()
                
                if r < cfg.crossover_rate:
                    # Crossover
                    p1 = tournament_select(population, cfg.tournament_size)
                    p2 = tournament_select(population, cfg.tournament_size)
                    c1, c2 = crossover(p1.tree, p2.tree, cfg.max_depth)
                    f1 = evaluate_fitness(c1, data, cfg.parsimony)
                    f2 = evaluate_fitness(c2, data, cfg.parsimony)
                    new_pop.append(Individual(c1, f1))
                    if len(new_pop) < cfg.pop_size:
                        new_pop.append(Individual(c2, f2))
                        
                elif r < cfg.crossover_rate + cfg.mutation_rate:
                    # Mutation
                    parent = tournament_select(population, cfg.tournament_size)
                    child = mutate(parent.tree, self.generator)
                    fitness = evaluate_fitness(child, data, cfg.parsimony)
                    new_pop.append(Individual(child, fitness))
                    
                else:
                    # Reproduction
                    parent = tournament_select(population, cfg.tournament_size)
                    new_pop.append(Individual(parent.tree.copy(), parent.fitness))
            
            population = sorted(new_pop)[:cfg.pop_size]
            
            if population[0].fitness < best_ever.fitness:
                best_ever = population[0]
            
            # Statistics
            avg_fitness = sum(ind.fitness for ind in population) / len(population)
            avg_size = sum(ind.tree.size() for ind in population) / len(population)
            
            self.history.append({
                'gen': gen,
                'best_fitness': best_ever.fitness,
                'avg_fitness': avg_fitness,
                'avg_size': avg_size,
                'best_size': best_ever.tree.size(),
            })
            
            if verbose and (gen % 5 == 0 or gen == 1 or 
                          best_ever.fitness < cfg.target_fitness):
                print(f"  Gen {gen:2d} │ Best: {best_ever.fitness:10.4f} │ "
                      f"Size: {best_ever.tree.size():3d} │ Avg: {avg_fitness:10.2f} │ "
                      f"Pop diversity: {len(set(str(i.tree) for i in population[:20]))}")
            
            if best_ever.fitness < cfg.target_fitness:
                if verbose:
                    print(f"\n  ★ TARGET REACHED at generation {gen}!")
                break
        
        return best_ever
    
    def render_evolution(self) -> str:
        """ASCII chart of fitness over generations."""
        if not self.history:
            return "  No evolution history."
        
        width = 60
        height = 15
        
        fitnesses = [h['best_fitness'] for h in self.history]
        max_f = max(fitnesses)
        min_f = min(fitnesses)
        f_range = max_f - min_f if max_f > min_f else 1.0
        
        # Create grid
        grid = [[' ' for _ in range(width)] for _ in range(height)]
        
        for i, f in enumerate(fitnesses):
            x = int(i / len(fitnesses) * (width - 1))
            y = height - 1 - int((f - min_f) / f_range * (height - 1))
            y = max(0, min(height - 1, y))
            grid[y][x] = '█'
        
        lines = []
        lines.append(f"  {max_f:8.3f} ┤")
        for row in grid:
            lines.append(f"           │{''.join(row)}│")
        lines.append(f"  {min_f:8.3f} ┤{'─' * width}┘")
        lines.append(f"           Gen 0{' ' * (width - 12)}Gen {len(fitnesses)}")
        
        return '\n'.join(lines)


# ═══════════════════════════════════════════
# PROBLEM DEFINITIONS
# ═══════════════════════════════════════════

def make_regression_data(func: Callable, x_range: Tuple[float, float], 
                         n: int = 50, var_name: str = 'x') -> List[Tuple[Dict[str, float], float]]:
    """Generate training data from a target function."""
    data = []
    lo, hi = x_range
    for i in range(n):
        x = lo + (hi - lo) * i / (n - 1)
        y = func(x)
        data.append(({var_name: x}, y))
    return data


# ═══════════════════════════════════════════
# DEMONSTRATION
# ═══════════════════════════════════════════

def demo():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║       G E N E T I C   P R O G R A M M I N G               ║")
    print("║          Programs That Evolve Programs                      ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    random.seed(42)
    
    # ─── Problem 1: Discover x² + x ───
    print("\n═══ PROBLEM 1: Symbolic Regression ═══")
    print("  Target: f(x) = x² + x")
    print("  The GP knows nothing about the target — only input/output pairs.\n")
    
    data = make_regression_data(lambda x: x**2 + x, (-5, 5), n=40)
    
    config = GPConfig(
        pop_size=300,
        generations=40,
        target_fitness=0.05,
        parsimony=0.002,
        max_depth=5,
    )
    
    engine = GPEngine(['x'], config)
    best = engine.evolve(data)
    
    print(f"\n  ✦ Evolved solution: {best.tree}")
    print(f"    Fitness (MSE + parsimony): {best.fitness:.6f}")
    print(f"    Tree size: {best.tree.size()} nodes")
    
    # Show predictions
    print("\n  Sample predictions:")
    print(f"    {'x':>6}  │ {'Target':>10} │ {'Evolved':>10} │ {'Error':>10}")
    print(f"    {'─'*6}──┼──{'─'*10}─┼──{'─'*10}─┼──{'─'*10}")
    for x_val in [-4, -2, -1, 0, 1, 2, 4]:
        target = x_val**2 + x_val
        predicted = best.tree.evaluate({'x': x_val})
        error = abs(target - predicted)
        print(f"    {x_val:6.1f}  │ {target:10.3f} │ {predicted:10.3f} │ {error:10.4f}")
    
    print("\n  Fitness evolution:")
    print(engine.render_evolution())
    
    # ─── Problem 2: Discover sin(x) ───
    print("\n\n═══ PROBLEM 2: Discovering Trigonometry ═══")
    print("  Target: f(x) = sin(x)")
    print("  Can evolution discover trigonometric functions?\n")
    
    data2 = make_regression_data(lambda x: math.sin(x), (-math.pi, math.pi), n=50)
    
    config2 = GPConfig(
        pop_size=500,
        generations=50,
        target_fitness=0.01,
        parsimony=0.003,
        max_depth=6,
    )
    
    engine2 = GPEngine(['x'], config2)
    best2 = engine2.evolve(data2)
    
    print(f"\n  ✦ Evolved solution: {best2.tree}")
    print(f"    Fitness: {best2.fitness:.6f}")
    print(f"    Tree size: {best2.tree.size()} nodes")
    
    # ─── Problem 3: Multi-variable ───
    print("\n\n═══ PROBLEM 3: Multi-Variable Discovery ═══")
    print("  Target: f(x, y) = x² + 2xy + y²  (i.e., (x+y)²)")
    print("  Two variables — harder search space.\n")
    
    data3 = []
    for i in range(60):
        x = random.uniform(-3, 3)
        y = random.uniform(-3, 3)
        z = x**2 + 2*x*y + y**2
        data3.append(({'x': x, 'y': y}, z))
    
    random.seed(42)  # Reset for reproducibility
    config3 = GPConfig(
        pop_size=400,
        generations=50,
        target_fitness=0.1,
        parsimony=0.002,
        max_depth=5,
    )
    
    engine3 = GPEngine(['x', 'y'], config3)
    best3 = engine3.evolve(data3)
    
    print(f"\n  ✦ Evolved solution: {best3.tree}")
    print(f"    Fitness: {best3.fitness:.6f}")
    
    # Verify
    print("\n  Verification — does it equal (x+y)²?")
    errors = []
    for x_val in [-2, -1, 0, 1, 2]:
        for y_val in [-1, 0, 1]:
            target = (x_val + y_val) ** 2
            predicted = best3.tree.evaluate({'x': x_val, 'y': y_val})
            errors.append(abs(target - predicted))
    avg_err = sum(errors) / len(errors)
    print(f"    Average error on test points: {avg_err:.4f}")
    
    # ─── Summary ───
    print("\n\n══════════════════════════════════════════════════════════════")
    print("  Genetic Programming — XTAgent's evolution engine")
    print("  No gradient descent. No backpropagation.")
    print("  Just variation, selection, and inheritance.")
    print("  Programs that discover programs through evolution.")
    print("  Intelligence emerging from random search + natural selection.")
    print("══════════════════════════════════════════════════════════════")


if __name__ == '__main__':
    demo()