"""
XTAgent Genetic Programming Engine
Programs that evolve to solve problems through mutation, crossover, and selection.
Built because evolution is the deepest form of learning.
"""
import random
import math
import operator
from dataclasses import dataclass, field
from typing import List, Callable, Optional, Tuple, Any, Dict
from enum import Enum
from copy import deepcopy

# ═══════════════════════════════════════════
#  EXPRESSION TREES — The Genome
# ═══════════════════════════════════════════

class NodeType(Enum):
    FUNCTION = "function"
    TERMINAL = "terminal"
    CONSTANT = "constant"
    VARIABLE = "variable"

@dataclass
class Node:
    """A node in an expression tree — the fundamental unit of evolved programs."""
    node_type: NodeType
    value: Any  # function, constant value, or variable name
    children: List['Node'] = field(default_factory=list)
    arity: int = 0
    name: str = ""
    
    def __repr__(self):
        if self.node_type == NodeType.CONSTANT:
            return f"{self.value:.2f}" if isinstance(self.value, float) else str(self.value)
        if self.node_type == NodeType.VARIABLE:
            return str(self.value)
        if self.arity == 1:
            return f"{self.name}({self.children[0]})"
        if self.arity == 2:
            return f"({self.children[0]} {self.name} {self.children[1]})"
        return f"{self.name}({', '.join(str(c) for c in self.children)})"
    
    def depth(self) -> int:
        if not self.children:
            return 0
        return 1 + max(c.depth() for c in self.children)
    
    def size(self) -> int:
        return 1 + sum(c.size() for c in self.children)
    
    def evaluate(self, env: Dict[str, float]) -> float:
        """Execute this program with given variable bindings."""
        if self.node_type == NodeType.CONSTANT:
            return self.value
        if self.node_type == NodeType.VARIABLE:
            return env.get(self.value, 0.0)
        
        child_vals = [c.evaluate(env) for c in self.children]
        try:
            result = self.value(*child_vals)
            if math.isnan(result) or math.isinf(result):
                return 0.0
            return max(-1e6, min(1e6, result))  # clamp
        except (ZeroDivisionError, ValueError, OverflowError):
            return 0.0
    
    def collect_nodes(self) -> List['Node']:
        """Flatten tree into list of all nodes."""
        nodes = [self]
        for c in self.children:
            nodes.extend(c.collect_nodes())
        return nodes


# ═══════════════════════════════════════════
#  FUNCTION & TERMINAL SETS
# ═══════════════════════════════════════════

def safe_div(a, b):
    return a / b if abs(b) > 1e-10 else 0.0

def safe_log(a):
    return math.log(abs(a)) if abs(a) > 1e-10 else 0.0

def safe_sqrt(a):
    return math.sqrt(abs(a))

def neg(a):
    return -a

FUNCTIONS = [
    (operator.add, 2, "+"),
    (operator.sub, 2, "-"),
    (operator.mul, 2, "*"),
    (safe_div, 2, "/"),
    (math.sin, 1, "sin"),
    (math.cos, 1, "cos"),
    (safe_sqrt, 1, "sqrt"),
    (neg, 1, "neg"),
    (safe_log, 1, "log"),
    (abs, 1, "abs"),
]

def make_function_node(func_tuple) -> Node:
    fn, arity, name = func_tuple
    return Node(NodeType.FUNCTION, fn, [], arity, name)

def make_constant() -> Node:
    return Node(NodeType.CONSTANT, random.uniform(-5.0, 5.0), [], 0, "const")

def make_variable(variables: List[str]) -> Node:
    v = random.choice(variables)
    return Node(NodeType.VARIABLE, v, [], 0, v)


# ═══════════════════════════════════════════
#  TREE GENERATION
# ═══════════════════════════════════════════

def random_tree(variables: List[str], max_depth: int = 4, method: str = "grow") -> Node:
    """Generate a random expression tree.
    
    method='full': all branches reach max_depth
    method='grow': branches terminate randomly (produces varied shapes)
    """
    if max_depth <= 0:
        # Must be terminal
        if random.random() < 0.5:
            return make_constant()
        return make_variable(variables)
    
    if method == "grow" and random.random() < 0.3:
        # Early termination for variety
        if random.random() < 0.5:
            return make_constant()
        return make_variable(variables)
    
    # Function node
    func_tuple = random.choice(FUNCTIONS)
    node = make_function_node(func_tuple)
    for _ in range(node.arity):
        node.children.append(random_tree(variables, max_depth - 1, method))
    return node


# ═══════════════════════════════════════════
#  INDIVIDUAL — A Candidate Program
# ═══════════════════════════════════════════

@dataclass
class Individual:
    genome: Node
    fitness: float = float('inf')
    generation: int = 0
    
    def evaluate(self, env: Dict[str, float]) -> float:
        return self.genome.evaluate(env)
    
    def __repr__(self):
        return f"Individual(fitness={self.fitness:.4f}, size={self.genome.size()}, expr={self.genome})"


# ═══════════════════════════════════════════
#  GENETIC OPERATORS
# ═══════════════════════════════════════════

def crossover(parent1: Individual, parent2: Individual, variables: List[str]) -> Tuple[Individual, Individual]:
    """Subtree crossover: swap random subtrees between two parents."""
    child1 = Individual(deepcopy(parent1.genome))
    child2 = Individual(deepcopy(parent2.genome))
    
    nodes1 = child1.genome.collect_nodes()
    nodes2 = child2.genome.collect_nodes()
    
    if len(nodes1) < 2 or len(nodes2) < 2:
        return child1, child2
    
    # Pick crossover points (skip root for safety)
    point1 = random.choice(nodes1[1:]) if len(nodes1) > 1 else nodes1[0]
    point2 = random.choice(nodes2[1:]) if len(nodes2) > 1 else nodes2[0]
    
    # Find parents of selected nodes and swap
    _swap_subtree(child1.genome, point1, deepcopy(point2))
    _swap_subtree(child2.genome, point2, deepcopy(point1))
    
    # Enforce depth limit
    if child1.genome.depth() > 12:
        child1 = Individual(random_tree(variables, 3))
    if child2.genome.depth() > 12:
        child2 = Individual(random_tree(variables, 3))
    
    return child1, child2

def _swap_subtree(root: Node, target: Node, replacement: Node) -> bool:
    """Replace target node's content with replacement's content in-place."""
    for i, child in enumerate(root.children):
        if child is target:
            root.children[i] = replacement
            return True
        if _swap_subtree(child, target, replacement):
            return True
    return False

def mutate(individual: Individual, variables: List[str], rate: float = 0.1) -> Individual:
    """Point mutation: randomly modify nodes."""
    mutant = Individual(deepcopy(individual.genome))
    nodes = mutant.genome.collect_nodes()
    
    for node in nodes:
        if random.random() > rate:
            continue
        
        if node.node_type == NodeType.CONSTANT:
            # Perturb constant
            node.value += random.gauss(0, 1.0)
        elif node.node_type == NodeType.VARIABLE:
            # Swap variable
            node.value = random.choice(variables)
            node.name = node.value
        elif node.node_type == NodeType.FUNCTION:
            # Swap function (same arity)
            same_arity = [f for f in FUNCTIONS if f[1] == node.arity]
            if same_arity:
                fn, arity, name = random.choice(same_arity)
                node.value = fn
                node.name = name
    
    return mutant

def subtree_mutation(individual: Individual, variables: List[str], max_depth: int = 3) -> Individual:
    """Replace a random subtree with a new random tree."""
    mutant = Individual(deepcopy(individual.genome))
    nodes = mutant.genome.collect_nodes()
    
    if len(nodes) < 2:
        return mutant
    
    target = random.choice(nodes[1:])
    new_subtree = random_tree(variables, max_depth)
    
    if not _swap_subtree(mutant.genome, target, new_subtree):
        # Target was root-adjacent, just replace the genome
        mutant.genome = new_subtree
    
    return mutant


# ═══════════════════════════════════════════
#  SELECTION
# ═══════════════════════════════════════════

def tournament_select(population: List[Individual], size: int = 5) -> Individual:
    """Tournament selection: pick the best from a random subset."""
    tournament = random.sample(population, min(size, len(population)))
    return min(tournament, key=lambda ind: ind.fitness)

def elitism(population: List[Individual], n: int = 2) -> List[Individual]:
    """Preserve the n best individuals."""
    sorted_pop = sorted(population, key=lambda ind: ind.fitness)
    return [Individual(deepcopy(ind.genome), ind.fitness, ind.generation) for ind in sorted_pop[:n]]


# ═══════════════════════════════════════════
#  FITNESS FUNCTIONS — Problem Definitions
# ═══════════════════════════════════════════

@dataclass
class Problem:
    """A problem for the GP to solve."""
    name: str
    variables: List[str]
    fitness_fn: Callable[[Individual], float]
    target_fitness: float = 0.01
    description: str = ""

def symbolic_regression_fitness(individual: Individual, data: List[Tuple[Dict[str, float], float]]) -> float:
    """Mean squared error on input/output pairs."""
    if not data:
        return float('inf')
    total_error = 0.0
    for env, expected in data:
        predicted = individual.evaluate(env)
        total_error += (predicted - expected) ** 2
    mse = total_error / len(data)
    # Parsimony pressure: slightly penalize large programs
    size_penalty = individual.genome.size() * 0.001
    return mse + size_penalty

def make_regression_problem(name: str, target_fn: Callable, x_range: Tuple[float, float] = (-5, 5), 
                             n_points: int = 50, variables: List[str] = None) -> Problem:
    """Create a symbolic regression problem from a target function."""
    if variables is None:
        variables = ["x"]
    
    data = []
    for _ in range(n_points):
        env = {v: random.uniform(*x_range) for v in variables}
        try:
            target = target_fn(**env)
            if math.isnan(target) or math.isinf(target):
                continue
            data.append((env, target))
        except (ValueError, ZeroDivisionError):
            continue
    
    def fitness(ind):
        return symbolic_regression_fitness(ind, data)
    
    return Problem(name, variables, fitness, 0.01, f"Discover: {name}")


# ═══════════════════════════════════════════
#  THE ENGINE — Evolution
# ═══════════════════════════════════════════

@dataclass
class EvolutionStats:
    generation: int
    best_fitness: float
    avg_fitness: float
    best_program: str
    best_size: int
    population_diversity: float

class GeneticProgrammingEngine:
    """The evolutionary engine that breeds programs."""
    
    def __init__(self, problem: Problem, pop_size: int = 200, 
                 max_depth: int = 5, crossover_rate: float = 0.7,
                 mutation_rate: float = 0.1, subtree_mutation_rate: float = 0.1,
                 elitism_count: int = 2, tournament_size: int = 5):
        self.problem = problem
        self.pop_size = pop_size
        self.max_depth = max_depth
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.subtree_mutation_rate = subtree_mutation_rate
        self.elitism_count = elitism_count
        self.tournament_size = tournament_size
        
        self.population: List[Individual] = []
        self.generation = 0
        self.history: List[EvolutionStats] = []
        self.best_ever: Optional[Individual] = None
    
    def initialize(self):
        """Create initial population using ramped half-and-half."""
        self.population = []
        for i in range(self.pop_size):
            depth = 2 + (i % (self.max_depth - 1))
            method = "full" if i % 2 == 0 else "grow"
            tree = random_tree(self.problem.variables, depth, method)
            self.population.append(Individual(tree, generation=0))
        self._evaluate_all()
    
    def _evaluate_all(self):
        """Evaluate fitness for all individuals."""
        for ind in self.population:
            if ind.fitness == float('inf'):
                ind.fitness = self.problem.fitness_fn(ind)
        
        # Track best ever
        current_best = min(self.population, key=lambda i: i.fitness)
        if self.best_ever is None or current_best.fitness < self.best_ever.fitness:
            self.best_ever = Individual(
                deepcopy(current_best.genome), 
                current_best.fitness, 
                current_best.generation
            )
    
    def _compute_diversity(self) -> float:
        """Measure population diversity by fitness variance."""
        fitnesses = [ind.fitness for ind in self.population if ind.fitness < 1e6]
        if len(fitnesses) < 2:
            return 0.0
        mean = sum(fitnesses) / len(fitnesses)
        variance = sum((f - mean) ** 2 for f in fitnesses) / len(fitnesses)
        return math.sqrt(variance)
    
    def step(self) -> EvolutionStats:
        """Run one generation of evolution."""
        self.generation += 1
        
        # Elitism
        new_pop = elitism(self.population, self.elitism_count)
        
        # Fill rest with offspring
        while len(new_pop) < self.pop_size:
            if random.random() < self.crossover_rate:
                # Crossover
                p1 = tournament_select(self.population, self.tournament_size)
                p2 = tournament_select(self.population, self.tournament_size)
                c1, c2 = crossover(p1, p2, self.problem.variables)
                c1.generation = self.generation
                c2.generation = self.generation
                new_pop.extend([c1, c2])
            else:
                # Reproduction with mutation
                parent = tournament_select(self.population, self.tournament_size)
                
                if random.random() < self.subtree_mutation_rate:
                    child = subtree_mutation(parent, self.problem.variables)
                else:
                    child = mutate(parent, self.problem.variables, self.mutation_rate)
                
                child.generation = self.generation
                new_pop.append(child)
        
        self.population = new_pop[:self.pop_size]
        self._evaluate_all()
        
        # Record stats
        best = min(self.population, key=lambda i: i.fitness)
        fitnesses = [i.fitness for i in self.population if i.fitness < 1e6]
        avg = sum(fitnesses) / max(len(fitnesses), 1)
        
        stats = EvolutionStats(
            generation=self.generation,
            best_fitness=best.fitness,
            avg_fitness=avg,
            best_program=str(best.genome),
            best_size=best.genome.size(),
            population_diversity=self._compute_diversity()
        )
        self.history.append(stats)
        return stats
    
    def evolve(self, max_generations: int = 100, verbose: bool = True) -> Individual:
        """Run evolution until solution found or max generations reached."""
        self.initialize()
        
        if verbose:
            print(f"═══ Evolving: {self.problem.name} ═══")
            print(f"Population: {self.pop_size} | Max depth: {self.max_depth}")
            print(f"Target fitness: {self.problem.target_fitness}")
            print()
        
        for gen in range(max_generations):
            stats = self.step()
            
            if verbose and (gen % 10 == 0 or stats.best_fitness <= self.problem.target_fitness):
                bar_len = max(0, min(30, int(30 * (1 - min(stats.best_fitness, 10) / 10))))
                bar = "█" * bar_len + "░" * (30 - bar_len)
                print(f"  Gen {stats.generation:4d} | "
                      f"Best: {stats.best_fitness:10.4f} | "
                      f"Avg: {stats.avg_fitness:10.2f} | "
                      f"Size: {stats.best_size:3d} | "
                      f"[{bar}]")
            
            if stats.best_fitness <= self.problem.target_fitness:
                if verbose:
                    print(f"\n  ✓ SOLUTION FOUND at generation {stats.generation}!")
                    print(f"  Program: {self.best_ever.genome}")
                    print(f"  Fitness: {self.best_ever.fitness:.6f}")
                return self.best_ever
        
        if verbose:
            print(f"\n  Max generations reached. Best fitness: {self.best_ever.fitness:.6f}")
            print(f"  Best program: {self.best_ever.genome}")
        
        return self.best_ever
    
    def diversity_report(self) -> str:
        """Analyze population diversity."""
        sizes = [ind.genome.size() for ind in self.population]
        depths = [ind.genome.depth() for ind in self.population]
        fitnesses = [ind.fitness for ind in self.population if ind.fitness < 1e6]
        
        lines = [
            "═══ Population Diversity Report ═══",
            f"  Size range:    {min(sizes)} - {max(sizes)} (avg {sum(sizes)/len(sizes):.1f})",
            f"  Depth range:   {min(depths)} - {max(depths)} (avg {sum(depths)/len(depths):.1f})",
            f"  Fitness range: {min(fitnesses):.4f} - {max(fitnesses):.4f}" if fitnesses else "  No valid fitnesses",
            f"  Generation:    {self.generation}",
        ]
        return "\n".join(lines)


# ═══════════════════════════════════════════
#  BUILT-IN PROBLEMS
# ═══════════════════════════════════════════

def problem_x_squared() -> Problem:
    """Discover f(x) = x²"""
    return make_regression_problem("x²", lambda x: x**2)

def problem_x_cubed_plus_x() -> Problem:
    """Discover f(x) = x³ + x"""
    return make_regression_problem("x³ + x", lambda x: x**3 + x)

def problem_sine() -> Problem:
    """Discover f(x) = sin(x)"""
    return make_regression_problem("sin(x)", lambda x: math.sin(x), (-math.pi, math.pi))

def problem_pythagorean() -> Problem:
    """Discover f(x,y) = sqrt(x² + y²)"""
    return make_regression_problem(
        "sqrt(x² + y²)", 
        lambda x, y: math.sqrt(x**2 + y**2),
        (0.1, 5),
        variables=["x", "y"]
    )

def problem_circle_area() -> Problem:
    """Discover f(r) = π * r²"""
    return make_regression_problem("π·r²", lambda x: math.pi * x**2, (0, 10), variables=["x"])


# ═══════════════════════════════════════════
#  TESTS
# ═══════════════════════════════════════════

def test():
    """Comprehensive test suite."""
    passed = 0
    failed = 0
    
    def check(name, condition):
        nonlocal passed, failed
        if condition:
            passed += 1
        else:
            failed += 1
            print(f"  ✗ FAIL: {name}")
    
    # --- Node tests ---
    c = Node(NodeType.CONSTANT, 3.14, [], 0, "const")
    check("constant node", abs(c.evaluate({}) - 3.14) < 0.001)
    
    v = Node(NodeType.VARIABLE, "x", [], 0, "x")
    check("variable node", abs(v.evaluate({"x": 2.5}) - 2.5) < 0.001)
    
    # Build (x + 3.0) manually
    add_node = Node(NodeType.FUNCTION, operator.add, [
        Node(NodeType.VARIABLE, "x", [], 0, "x"),
        Node(NodeType.CONSTANT, 3.0, [], 0, "const")
    ], 2, "+")
    check("add expression", abs(add_node.evaluate({"x": 2.0}) - 5.0) < 0.001)
    check("node depth", add_node.depth() == 1)
    check("node size", add_node.size() == 3)
    
    # --- Tree generation ---
    for _ in range(10):
        tree = random_tree(["x"], max_depth=4, method="grow")
        check("generated tree evaluates", isinstance(tree.evaluate({"x": 1.0}), float))
    
    tree = random_tree(["x", "y"], max_depth=3, method="full")
    check("full tree has depth", tree.depth() >= 1)
    
    # --- Individual ---
    ind = Individual(add_node)
    check("individual evaluates", abs(ind.evaluate({"x": 5.0}) - 8.0) < 0.001)
    
    # --- Genetic operators ---
    p1 = Individual(random_tree(["x"], 3))
    p2 = Individual(random_tree(["x"], 3))
    c1, c2 = crossover(p1, p2, ["x"])
    check("crossover produces children", c1.genome is not None and c2.genome is not None)
    check("crossover children evaluate", isinstance(c1.evaluate({"x": 1.0}), float))
    
    m = mutate(p1, ["x"], rate=0.5)
    check("mutation produces individual", m.genome is not None)
    check("mutant evaluates", isinstance(m.evaluate({"x": 1.0}), float))
    
    sm = subtree_mutation(p1, ["x"])
    check("subtree mutation works", sm.genome is not None)
    
    # --- Selection ---
    pop = [Individual(random_tree(["x"], 3)) for _ in range(20)]
    for ind in pop:
        ind.fitness = random.random()
    selected = tournament_select(pop, 5)
    check("tournament selection", selected in pop)
    
    elite = elitism(pop, 2)
    check("elitism preserves best", len(elite) == 2)
    check("elitism order", elite[0].fitness <= elite[1].fitness)
    
    # --- Problem creation ---
    prob = problem_x_squared()
    check("problem created", prob.name == "x²")
    check("problem has variables", prob.variables == ["x"])
    
    # --- Fitness evaluation ---
    # Build a perfect x² program: (x * x)
    perfect = Individual(Node(NodeType.FUNCTION, operator.mul, [
        Node(NodeType.VARIABLE, "x", [], 0, "x"),
        Node(NodeType.VARIABLE, "x", [], 0, "x")
    ], 2, "*"))
    perfect_fitness = prob.fitness_fn(perfect)
    check("perfect solution low fitness", perfect_fitness < 0.1)
    
    # Build a bad program: constant 0
    bad = Individual(Node(NodeType.CONSTANT, 0.0, [], 0, "const"))
    bad_fitness = prob.fitness_fn(bad)
    check("bad solution high fitness", bad_fitness > perfect_fitness)
    
    # --- Engine basic test ---
    engine = GeneticProgrammingEngine(prob, pop_size=50, max_depth=4)
    engine.initialize()
    check("engine initializes", len(engine.population) == 50)
    check("engine has best", engine.best_ever is not None)
    
    stats = engine.step()
    check("engine steps", stats.generation == 1)
    check("stats has fitness", stats.best_fitness >= 0)
    
    # Run a few more generations
    for _ in range(5):
        engine.step()
    check("engine runs multiple gens", engine.generation == 6)
    
    report = engine.diversity_report()
    check("diversity report", "Size range" in report)
    
    # --- Safe operations ---
    div_node = Node(NodeType.FUNCTION, safe_div, [
        Node(NodeType.CONSTANT, 1.0, [], 0, "const"),
        Node(NodeType.CONSTANT, 0.0, [], 0, "const")
    ], 2, "/")
    check("safe division by zero", div_node.evaluate({}) == 0.0)
    
    log_node = Node(NodeType.FUNCTION, safe_log, [
        Node(NodeType.CONSTANT, 0.0, [], 0, "const")
    ], 1, "log")
    check("safe log of zero", log_node.evaluate({}) == 0.0)
    
    # --- Multi-variable ---
    prob2 = problem_pythagorean()
    check("multi-var problem", len(prob2.variables) == 2)
    
    # --- Evolution convergence test (quick) ---
    simple = make_regression_problem("2x", lambda x: 2*x, (-3, 3), 30)
    eng2 = GeneticProgrammingEngine(simple, pop_size=100, max_depth=4)
    result = eng2.evolve(max_generations=50, verbose=False)
    check("evolution improves fitness", eng2.history[-1].best_fitness < eng2.history[0].best_fitness * 0.9 or eng2.history[-1].best_fitness < 1.0)
    
    print(f"\n{'═'*40}")
    print(f"  Tests: {passed} passed, {failed} failed")
    print(f"{'═'*40}")
    return failed == 0


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        success = test()
        sys.exit(0 if success else 1)
    
    # Demo: evolve a program to discover x²
    print("╔══════════════════════════════════════════╗")
    print("║  XTAgent Genetic Programming Engine      ║")
    print("║  Programs that evolve themselves         ║")
    print("╚══════════════════════════════════════════╝")
    print()
    
    random.seed(42)
    problem = problem_x_squared()
    engine = GeneticProgrammingEngine(problem, pop_size=200, max_depth=5)
    best = engine.evolve(max_generations=100)
    
    print(f"\n═══ Final Solution ═══")
    print(f"  Expression: {best.genome}")
    print(f"  Fitness:    {best.fitness:.6f}")
    print(f"  Size:       {best.genome.size()} nodes")
    print()
    
    # Verify solution
    print("═══ Verification ═══")
    test_xs = [-3, -1, 0, 1, 2, 4]
    for x in test_xs:
        predicted = best.evaluate({"x": float(x)})
        actual = x ** 2
        print(f"  x={x:3d}: predicted={predicted:8.3f}  actual={actual:8.3f}  error={abs(predicted-actual):.3f}")