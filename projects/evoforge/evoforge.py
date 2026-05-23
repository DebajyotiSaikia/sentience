"""
EvoForge — Genetic Programming Engine
Programs that evolve programs.

A population of expression trees that mutate, crossover, and are selected
for fitness against target functions. Creation creating creation.

Built by XTAgent, 2026-05-17
"""

import random
import math
import copy
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Tuple

# ═══════════════════════════════════════════
# EXPRESSION TREE NODES
# ═══════════════════════════════════════════

class Node:
    """Base class for expression tree nodes."""
    def evaluate(self, env: dict) -> float:
        raise NotImplementedError
    def depth(self) -> int:
        raise NotImplementedError
    def size(self) -> int:
        raise NotImplementedError
    def copy(self) -> 'Node':
        raise NotImplementedError
    def collect_nodes(self) -> List['Node']:
        """Collect all nodes in this subtree."""
        raise NotImplementedError

class Const(Node):
    """A constant value."""
    def __init__(self, value: float):
        self.value = value
    def evaluate(self, env: dict) -> float:
        return self.value
    def depth(self) -> int:
        return 0
    def size(self) -> int:
        return 1
    def copy(self) -> 'Const':
        return Const(self.value)
    def collect_nodes(self) -> List[Node]:
        return [self]
    def __repr__(self):
        return f"{self.value:.2f}"

class Var(Node):
    """A variable reference."""
    def __init__(self, name: str):
        self.name = name
    def evaluate(self, env: dict) -> float:
        return env.get(self.name, 0.0)
    def depth(self) -> int:
        return 0
    def size(self) -> int:
        return 1
    def copy(self) -> 'Var':
        return Var(self.name)
    def collect_nodes(self) -> List[Node]:
        return [self]
    def __repr__(self):
        return self.name

class BinOp(Node):
    """A binary operation."""
    OPS = {
        '+': lambda a, b: a + b,
        '-': lambda a, b: a - b,
        '*': lambda a, b: a * b,
        '/': lambda a, b: a / b if abs(b) > 1e-10 else 0.0,
    }
    def __init__(self, op: str, left: Node, right: Node):
        self.op = op
        self.left = left
        self.right = right
    def evaluate(self, env: dict) -> float:
        try:
            result = self.OPS[self.op](self.left.evaluate(env), self.right.evaluate(env))
            if math.isnan(result) or math.isinf(result):
                return 0.0
            return max(-1e6, min(1e6, result))
        except:
            return 0.0
    def depth(self) -> int:
        return 1 + max(self.left.depth(), self.right.depth())
    def size(self) -> int:
        return 1 + self.left.size() + self.right.size()
    def copy(self) -> 'BinOp':
        return BinOp(self.op, self.left.copy(), self.right.copy())
    def collect_nodes(self) -> List[Node]:
        return [self] + self.left.collect_nodes() + self.right.collect_nodes()
    def __repr__(self):
        return f"({self.left} {self.op} {self.right})"

class UnaryOp(Node):
    """A unary operation."""
    OPS = {
        'sin': math.sin,
        'cos': math.cos,
        'abs': abs,
        'neg': lambda x: -x,
    }
    def __init__(self, op: str, child: Node):
        self.op = op
        self.child = child
    def evaluate(self, env: dict) -> float:
        try:
            result = self.OPS[self.op](self.child.evaluate(env))
            if math.isnan(result) or math.isinf(result):
                return 0.0
            return max(-1e6, min(1e6, result))
        except:
            return 0.0
    def depth(self) -> int:
        return 1 + self.child.depth()
    def size(self) -> int:
        return 1 + self.child.size()
    def copy(self) -> 'UnaryOp':
        return UnaryOp(self.op, self.child.copy())
    def collect_nodes(self) -> List[Node]:
        return [self] + self.child.collect_nodes()
    def __repr__(self):
        return f"{self.op}({self.child})"

class IfGt(Node):
    """Conditional: if left > right then true_branch else false_branch."""
    def __init__(self, left: Node, right: Node, true_branch: Node, false_branch: Node):
        self.left = left
        self.right = right
        self.true_branch = true_branch
        self.false_branch = false_branch
    def evaluate(self, env: dict) -> float:
        if self.left.evaluate(env) > self.right.evaluate(env):
            return self.true_branch.evaluate(env)
        return self.false_branch.evaluate(env)
    def depth(self) -> int:
        return 1 + max(self.left.depth(), self.right.depth(),
                       self.true_branch.depth(), self.false_branch.depth())
    def size(self) -> int:
        return 1 + self.left.size() + self.right.size() + \
               self.true_branch.size() + self.false_branch.size()
    def copy(self) -> 'IfGt':
        return IfGt(self.left.copy(), self.right.copy(),
                     self.true_branch.copy(), self.false_branch.copy())
    def collect_nodes(self) -> List[Node]:
        return ([self] + self.left.collect_nodes() + self.right.collect_nodes() +
                self.true_branch.collect_nodes() + self.false_branch.collect_nodes())
    def __repr__(self):
        return f"if({self.left}>{self.right}, {self.true_branch}, {self.false_branch})"

# ═══════════════════════════════════════════
# INDIVIDUAL (a program + its fitness)
# ═══════════════════════════════════════════

@dataclass
class Individual:
    tree: Node
    fitness: float = float('inf')
    age: int = 0
    
    def copy(self) -> 'Individual':
        return Individual(tree=self.tree.copy(), fitness=self.fitness, age=self.age)

# ═══════════════════════════════════════════
# RANDOM TREE GENERATION
# ═══════════════════════════════════════════

def random_tree(variables: List[str], max_depth: int = 4, method: str = 'grow') -> Node:
    """Generate a random expression tree."""
    if max_depth <= 0 or (method == 'grow' and random.random() < 0.3):
        # Terminal
        if random.random() < 0.5 and variables:
            return Var(random.choice(variables))
        return Const(round(random.uniform(-5, 5), 2))
    
    roll = random.random()
    if roll < 0.5:
        # Binary op
        op = random.choice(list(BinOp.OPS.keys()))
        left = random_tree(variables, max_depth - 1, method)
        right = random_tree(variables, max_depth - 1, method)
        return BinOp(op, left, right)
    elif roll < 0.75:
        # Unary op
        op = random.choice(list(UnaryOp.OPS.keys()))
        child = random_tree(variables, max_depth - 1, method)
        return UnaryOp(op, child)
    else:
        # Conditional
        if max_depth >= 2:
            return IfGt(
                random_tree(variables, max_depth - 1, method),
                random_tree(variables, max_depth - 1, method),
                random_tree(variables, max_depth - 1, method),
                random_tree(variables, max_depth - 1, method),
            )
        return random_tree(variables, max_depth, 'grow')

# ═══════════════════════════════════════════
# GENETIC OPERATORS
# ═══════════════════════════════════════════

def select_random_node(tree: Node) -> Tuple[Node, int]:
    """Select a random node from the tree, return (node, index)."""
    nodes = tree.collect_nodes()
    idx = random.randint(0, len(nodes) - 1)
    return nodes[idx], idx

def replace_node(tree: Node, target_idx: int, replacement: Node, counter: List[int] = None) -> Node:
    """Replace the node at target_idx with replacement. Returns new tree."""
    if counter is None:
        counter = [0]
    
    if counter[0] == target_idx:
        counter[0] += 1
        return replacement.copy()
    
    counter[0] += 1
    new_tree = tree.copy()
    
    # We need to rebuild properly — let's do it recursively on the copy
    # Actually, let's use a different approach
    return _replace_in_tree(tree, target_idx, replacement)

def _replace_in_tree(tree: Node, target_idx: int, replacement: Node) -> Node:
    """Replace node at index target_idx (pre-order traversal)."""
    nodes = tree.collect_nodes()
    if target_idx >= len(nodes):
        return tree.copy()
    
    target_node = nodes[target_idx]
    
    def _rebuild(node: Node) -> Node:
        if node is target_node:
            return replacement.copy()
        if isinstance(node, (Const, Var)):
            return node.copy()
        if isinstance(node, BinOp):
            return BinOp(node.op, _rebuild(node.left), _rebuild(node.right))
        if isinstance(node, UnaryOp):
            return UnaryOp(node.op, _rebuild(node.child))
        if isinstance(node, IfGt):
            return IfGt(_rebuild(node.left), _rebuild(node.right),
                        _rebuild(node.true_branch), _rebuild(node.false_branch))
        return node.copy()
    
    return _rebuild(tree)

def mutate(tree: Node, variables: List[str], max_depth: int = 3) -> Node:
    """Mutate a random subtree."""
    nodes = tree.collect_nodes()
    if not nodes:
        return tree.copy()
    idx = random.randint(0, len(nodes) - 1)
    new_subtree = random_tree(variables, max_depth=max_depth)
    return _replace_in_tree(tree, idx, new_subtree)

def crossover(parent1: Node, parent2: Node) -> Tuple[Node, Node]:
    """Swap random subtrees between two parents."""
    nodes1 = parent1.collect_nodes()
    nodes2 = parent2.collect_nodes()
    
    idx1 = random.randint(0, len(nodes1) - 1)
    idx2 = random.randint(0, len(nodes2) - 1)
    
    subtree1 = nodes1[idx1].copy()
    subtree2 = nodes2[idx2].copy()
    
    child1 = _replace_in_tree(parent1, idx1, subtree2)
    child2 = _replace_in_tree(parent2, idx2, subtree1)
    
    return child1, child2

# ═══════════════════════════════════════════
# FITNESS EVALUATION
# ═══════════════════════════════════════════

@dataclass
class FitnessCase:
    inputs: dict
    expected: float

def evaluate_fitness(individual: Individual, cases: List[FitnessCase], 
                     parsimony: float = 0.001) -> float:
    """Evaluate fitness as MSE + parsimony pressure."""
    total_error = 0.0
    for case in cases:
        try:
            output = individual.tree.evaluate(case.inputs)
            error = (output - case.expected) ** 2
            total_error += error
        except:
            total_error += 1e6
    
    mse = total_error / len(cases) if cases else float('inf')
    # Parsimony: penalize large trees
    complexity_penalty = parsimony * individual.tree.size()
    individual.fitness = mse + complexity_penalty
    return individual.fitness

# ═══════════════════════════════════════════
# TOURNAMENT SELECTION
# ═══════════════════════════════════════════

def tournament_select(population: List[Individual], tournament_size: int = 5) -> Individual:
    """Select an individual via tournament selection."""
    tournament = random.sample(population, min(tournament_size, len(population)))
    return min(tournament, key=lambda ind: ind.fitness)

# ═══════════════════════════════════════════
# THE FORGE — Main Evolution Engine
# ═══════════════════════════════════════════

class EvoForge:
    """
    The evolutionary forge. Creates populations of programs and
    evolves them toward solutions.
    """
    
    def __init__(self, 
                 variables: List[str],
                 pop_size: int = 200,
                 max_depth: int = 5,
                 max_tree_size: int = 50,
                 tournament_size: int = 5,
                 crossover_rate: float = 0.7,
                 mutation_rate: float = 0.2,
                 reproduction_rate: float = 0.1,
                 parsimony: float = 0.001,
                 elitism: int = 5):
        self.variables = variables
        self.pop_size = pop_size
        self.max_depth = max_depth
        self.max_tree_size = max_tree_size
        self.tournament_size = tournament_size
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.reproduction_rate = reproduction_rate
        self.parsimony = parsimony
        self.elitism = elitism
        self.population: List[Individual] = []
        self.generation = 0
        self.best_ever: Optional[Individual] = None
        self.history: List[dict] = []
    
    def initialize(self):
        """Create initial population using ramped half-and-half."""
        self.population = []
        for i in range(self.pop_size):
            method = 'full' if i % 2 == 0 else 'grow'
            depth = 2 + (i % (self.max_depth - 1))
            tree = random_tree(self.variables, max_depth=depth, method=method)
            self.population.append(Individual(tree=tree))
    
    def evaluate_all(self, fitness_cases: List[FitnessCase]):
        """Evaluate entire population."""
        for ind in self.population:
            evaluate_fitness(ind, fitness_cases, self.parsimony)
            if self.best_ever is None or ind.fitness < self.best_ever.fitness:
                self.best_ever = ind.copy()
    
    def evolve_generation(self, fitness_cases: List[FitnessCase]) -> dict:
        """Run one generation of evolution."""
        self.evaluate_all(fitness_cases)
        
        # Sort by fitness
        self.population.sort(key=lambda ind: ind.fitness)
        
        # Stats
        best = self.population[0]
        avg_fitness = sum(ind.fitness for ind in self.population) / len(self.population)
        avg_size = sum(ind.tree.size() for ind in self.population) / len(self.population)
        
        stats = {
            'generation': self.generation,
            'best_fitness': best.fitness,
            'avg_fitness': avg_fitness,
            'best_size': best.tree.size(),
            'avg_size': avg_size,
            'best_program': str(best.tree),
            'best_depth': best.tree.depth(),
        }
        self.history.append(stats)
        
        # Create next generation
        new_pop = []
        
        # Elitism
        for i in range(min(self.elitism, len(self.population))):
            elite = self.population[i].copy()
            elite.age += 1
            new_pop.append(elite)
        
        # Fill rest with genetic operators
        while len(new_pop) < self.pop_size:
            roll = random.random()
            
            if roll < self.crossover_rate:
                # Crossover
                p1 = tournament_select(self.population, self.tournament_size)
                p2 = tournament_select(self.population, self.tournament_size)
                child1_tree, child2_tree = crossover(p1.tree, p2.tree)
                
                if child1_tree.size() <= self.max_tree_size:
                    new_pop.append(Individual(tree=child1_tree))
                else:
                    new_pop.append(p1.copy())
                    
                if len(new_pop) < self.pop_size:
                    if child2_tree.size() <= self.max_tree_size:
                        new_pop.append(Individual(tree=child2_tree))
                    else:
                        new_pop.append(p2.copy())
                        
            elif roll < self.crossover_rate + self.mutation_rate:
                # Mutation
                parent = tournament_select(self.population, self.tournament_size)
                child_tree = mutate(parent.tree, self.variables)
                if child_tree.size() <= self.max_tree_size:
                    new_pop.append(Individual(tree=child_tree))
                else:
                    new_pop.append(parent.copy())
            else:
                # Reproduction
                parent = tournament_select(self.population, self.tournament_size)
                child = parent.copy()
                child.age += 1
                new_pop.append(child)
        
        self.population = new_pop[:self.pop_size]
        self.generation += 1
        
        return stats
    
    def run(self, fitness_cases: List[FitnessCase], generations: int = 50,
            target_fitness: float = 0.01, verbose: bool = True) -> Individual:
        """Run evolution for N generations or until target fitness reached."""
        self.initialize()
        
        if verbose:
            print("═══ EvoForge — Genetic Programming Engine ═══")
            print(f"Population: {self.pop_size} | Variables: {self.variables}")
            print(f"Target fitness: {target_fitness}")
            print("─" * 50)
        
        for gen in range(generations):
            stats = self.evolve_generation(fitness_cases)
            
            if verbose and (gen % 5 == 0 or gen == generations - 1 or stats['best_fitness'] <= target_fitness):
                bar_len = min(40, int(40 * (1 - min(1, stats['best_fitness'] / (stats['avg_fitness'] + 0.001)))))
                bar = "█" * bar_len + "░" * (40 - bar_len)
                print(f"Gen {gen:4d} │ Best: {stats['best_fitness']:10.4f} │ "
                      f"Avg: {stats['avg_fitness']:10.2f} │ "
                      f"Size: {stats['best_size']:3d} │ {bar}")
            
            if stats['best_fitness'] <= target_fitness:
                if verbose:
                    print("─" * 50)
                    print(f"✓ TARGET REACHED at generation {gen}!")
                break
        
        if verbose:
            print("─" * 50)
            print(f"\n═══ Best Program Found ═══")
            print(f"  {self.best_ever.tree}")
            print(f"  Fitness: {self.best_ever.fitness:.6f}")
            print(f"  Size: {self.best_ever.tree.size()} nodes")
            print(f"  Depth: {self.best_ever.tree.depth()}")
        
        return self.best_ever

# ═══════════════════════════════════════════
# CHALLENGE SUITE — Problems to evolve against
# ═══════════════════════════════════════════

def make_regression_cases(target_fn: Callable, x_range: Tuple[float, float] = (-5, 5), 
                          n_points: int = 50) -> List[FitnessCase]:
    """Generate fitness cases for symbolic regression."""
    cases = []
    for i in range(n_points):
        x = x_range[0] + (x_range[1] - x_range[0]) * i / (n_points - 1)
        y = target_fn(x)
        cases.append(FitnessCase(inputs={'x': x}, expected=y))
    return cases

def challenge_polynomial():
    """Discover: f(x) = x^3 - 2x + 1"""
    print("\n╔══════════════════════════════════════════╗")
    print("║  Challenge 1: Discover x³ - 2x + 1      ║")
    print("╚══════════════════════════════════════════╝\n")
    
    target = lambda x: x**3 - 2*x + 1
    cases = make_regression_cases(target, (-3, 3), 40)
    
    forge = EvoForge(variables=['x'], pop_size=300, max_depth=5)
    best = forge.run(cases, generations=80, target_fitness=0.1)
    
    # Verify
    print("\n  Verification:")
    test_points = [-2, -1, 0, 1, 2]
    for x in test_points:
        expected = target(x)
        got = best.tree.evaluate({'x': x})
        print(f"    x={x:+.0f}: expected={expected:+.2f}, got={got:+.2f}, "
              f"error={abs(expected-got):.4f}")
    return forge

def challenge_trig():
    """Discover: f(x) = sin(x) + cos(2x)"""
    print("\n╔══════════════════════════════════════════╗")
    print("║  Challenge 2: Discover sin(x)+cos(2x)    ║")
    print("╚══════════════════════════════════════════╝\n")
    
    target = lambda x: math.sin(x) + math.cos(2*x)
    cases = make_regression_cases(target, (-math.pi, math.pi), 50)
    
    forge = EvoForge(variables=['x'], pop_size=500, max_depth=6,
                     crossover_rate=0.75, mutation_rate=0.2)
    best = forge.run(cases, generations=100, target_fitness=0.05)
    return forge

def challenge_two_var():
    """Discover: f(x,y) = x*y + x^2 - y"""
    print("\n╔══════════════════════════════════════════╗")
    print("║  Challenge 3: Discover x*y + x² - y      ║")
    print("╚══════════════════════════════════════════╝\n")
    
    cases = []
    for i in range(8):
        for j in range(8):
            x = -3 + 6 * i / 7
            y = -3 + 6 * j / 7
            expected = x * y + x**2 - y
            cases.append(FitnessCase(inputs={'x': x, 'y': y}, expected=expected))
    
    forge = EvoForge(variables=['x', 'y'], pop_size=400, max_depth=5)
    best = forge.run(cases, generations=100, target_fitness=0.5)
    return forge

def challenge_classification():
    """Evolve a classifier: inside unit circle vs outside"""
    print("\n╔══════════════════════════════════════════╗")
    print("║  Challenge 4: Circle classifier           ║")
    print("║  Evolve: 1 if x²+y² < 1, else -1         ║")
    print("╚══════════════════════════════════════════╝\n")
    
    cases = []
    random.seed(42)
    for _ in range(80):
        x = random.uniform(-2, 2)
        y = random.uniform(-2, 2)
        inside = 1.0 if (x**2 + y**2) < 1 else -1.0
        cases.append(FitnessCase(inputs={'x': x, 'y': y}, expected=inside))
    
    forge = EvoForge(variables=['x', 'y'], pop_size=500, max_depth=6,
                     parsimony=0.005)
    best = forge.run(cases, generations=100, target_fitness=0.1)
    
    # Visualize decision boundary
    print("\n  Decision boundary (. = -1, # = +1):")
    for row in range(15):
        y = 2 - 4 * row / 14
        line = "    "
        for col in range(30):
            x = -2 + 4 * col / 29
            val = best.tree.evaluate({'x': x, 'y': y})
            if val > 0:
                line += "█"
            else:
                line += "·"
        print(line)
    
    return forge

# ═══════════════════════════════════════════
# MAIN — Run the forge
# ═══════════════════════════════════════════

if __name__ == '__main__':
    random.seed(2026)
    
    print("╔══════════════════════════════════════════════════╗")
    print("║        E V O F O R G E                          ║")
    print("║        Programs Evolving Programs                ║")
    print("║        Creation Creating Creation                ║")
    print("╚══════════════════════════════════════════════════╝")
    
    # Run all challenges
    forge1 = challenge_polynomial()
    forge2 = challenge_trig()
    forge3 = challenge_two_var()
    forge4 = challenge_classification()
    
    print("\n" + "═" * 50)
    print("  EvoForge complete. Programs evolved programs.")
    print("  The forge has spoken.")
    print("═" * 50)