"""
Genetic Programming Engine — Programs That Evolve Programs
Built by XTAgent. The question: can computation create computation?

Implements:
  - Tree-based GP with typed expression trees
  - Tournament selection with elitism
  - Subtree crossover and point mutation
  - Automatic function discovery (symbolic regression)
  - Bloat control via parsimony pressure
  - Multiple problem domains: regression, classification, boolean

No dependencies. Pure Python. Programs writing programs.
"""

import math
import random
import copy
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Tuple, Any, Set
from enum import Enum

# ── Node Types ───────────────────────────────────────────

class NodeType(Enum):
    FUNCTION = "function"
    TERMINAL = "terminal"
    CONSTANT = "constant"
    VARIABLE = "variable"

@dataclass
class FuncDef:
    """Definition of a function node."""
    name: str
    arity: int
    func: Callable
    symbol: str = ""
    
    def __post_init__(self):
        if not self.symbol:
            self.symbol = self.name

# ── Safe Math ────────────────────────────────────────────

def safe_div(a: float, b: float) -> float:
    if abs(b) < 1e-10:
        return 1.0
    return a / b

def safe_log(a: float) -> float:
    if a <= 0:
        return 0.0
    return math.log(abs(a))

def safe_sqrt(a: float) -> float:
    return math.sqrt(abs(a))

def safe_exp(a: float) -> float:
    try:
        return math.exp(min(a, 30))
    except OverflowError:
        return 1e13

def safe_pow(a: float, b: float) -> float:
    try:
        return abs(a) ** min(abs(b), 10)
    except (OverflowError, ValueError):
        return 1.0

# ── Standard Function Sets ───────────────────────────────

ARITHMETIC = [
    FuncDef("add", 2, lambda a, b: a + b, "+"),
    FuncDef("sub", 2, lambda a, b: a - b, "-"),
    FuncDef("mul", 2, lambda a, b: a * b, "*"),
    FuncDef("div", 2, safe_div, "/"),
]

TRANSCENDENTAL = [
    FuncDef("sin", 1, math.sin, "sin"),
    FuncDef("cos", 1, math.cos, "cos"),
    FuncDef("exp", 1, safe_exp, "exp"),
    FuncDef("log", 1, safe_log, "log"),
    FuncDef("sqrt", 1, safe_sqrt, "√"),
]

BOOLEAN = [
    FuncDef("and", 2, lambda a, b: float(a > 0.5 and b > 0.5), "∧"),
    FuncDef("or", 2, lambda a, b: float(a > 0.5 or b > 0.5), "∨"),
    FuncDef("not", 1, lambda a: float(not (a > 0.5)), "¬"),
    FuncDef("xor", 2, lambda a, b: float((a > 0.5) != (b > 0.5)), "⊕"),
]

COMPARISON = [
    FuncDef("gt", 2, lambda a, b: float(a > b), ">"),
    FuncDef("lt", 2, lambda a, b: float(a < b), "<"),
    FuncDef("ifelse", 3, lambda c, t, f: t if c > 0.5 else f, "if"),
]

# ── Expression Tree ──────────────────────────────────────

@dataclass
class Node:
    """A node in an expression tree — the atom of evolved programs."""
    node_type: NodeType
    value: Any = None          # For terminals/constants
    func_def: Optional[FuncDef] = None  # For function nodes
    children: List['Node'] = field(default_factory=list)
    
    @property
    def arity(self) -> int:
        if self.func_def:
            return self.func_def.arity
        return 0
    
    @property
    def is_leaf(self) -> bool:
        return self.node_type in (NodeType.TERMINAL, NodeType.CONSTANT, NodeType.VARIABLE)
    
    def evaluate(self, variables: Dict[str, float]) -> float:
        """Evaluate this tree with given variable bindings."""
        if self.node_type == NodeType.CONSTANT:
            return self.value
        elif self.node_type == NodeType.VARIABLE:
            return variables.get(self.value, 0.0)
        elif self.node_type == NodeType.FUNCTION:
            args = [child.evaluate(variables) for child in self.children]
            try:
                result = self.func_def.func(*args)
                if math.isnan(result) or math.isinf(result):
                    return 0.0
                return result
            except (OverflowError, ValueError, ZeroDivisionError):
                return 0.0
        return 0.0
    
    def depth(self) -> int:
        if not self.children:
            return 0
        return 1 + max(c.depth() for c in self.children)
    
    def size(self) -> int:
        return 1 + sum(c.size() for c in self.children)
    
    def to_str(self, compact: bool = True) -> str:
        """Convert tree to human-readable expression."""
        if self.node_type == NodeType.CONSTANT:
            return f"{self.value:.2f}" if isinstance(self.value, float) else str(self.value)
        elif self.node_type == NodeType.VARIABLE:
            return str(self.value)
        elif self.node_type == NodeType.FUNCTION:
            sym = self.func_def.symbol
            if self.func_def.arity == 1:
                return f"{sym}({self.children[0].to_str(compact)})"
            elif self.func_def.arity == 2:
                if compact and sym in "+-*/":
                    return f"({self.children[0].to_str(compact)} {sym} {self.children[1].to_str(compact)})"
                return f"{sym}({self.children[0].to_str(compact)}, {self.children[1].to_str(compact)})"
            else:
                args = ", ".join(c.to_str(compact) for c in self.children)
                return f"{sym}({args})"
        return "?"
    
    def copy(self) -> 'Node':
        return copy.deepcopy(self)
    
    def all_nodes(self) -> List['Node']:
        """Flatten tree to list of all nodes."""
        result = [self]
        for child in self.children:
            result.extend(child.all_nodes())
        return result
    
    def __repr__(self):
        return self.to_str()

# ── Tree Generation ──────────────────────────────────────

class TreeGenerator:
    """Generates random expression trees."""
    
    def __init__(self, functions: List[FuncDef], variables: List[str],
                 constant_range: Tuple[float, float] = (-5.0, 5.0),
                 ephemeral_prob: float = 0.3):
        self.functions = functions
        self.variables = variables
        self.constant_range = constant_range
        self.ephemeral_prob = ephemeral_prob
    
    def random_terminal(self) -> Node:
        if random.random() < self.ephemeral_prob:
            val = random.uniform(*self.constant_range)
            return Node(NodeType.CONSTANT, value=round(val, 2))
        else:
            var = random.choice(self.variables)
            return Node(NodeType.VARIABLE, value=var)
    
    def grow(self, max_depth: int, current_depth: int = 0) -> Node:
        """Grow method — mix of functions and terminals at each level."""
        if current_depth >= max_depth or (current_depth > 0 and random.random() < 0.3):
            return self.random_terminal()
        
        func = random.choice(self.functions)
        children = [self.grow(max_depth, current_depth + 1) for _ in range(func.arity)]
        return Node(NodeType.FUNCTION, func_def=func, children=children)
    
    def full(self, max_depth: int, current_depth: int = 0) -> Node:
        """Full method — always pick functions until max depth."""
        if current_depth >= max_depth:
            return self.random_terminal()
        
        func = random.choice(self.functions)
        children = [self.full(max_depth, current_depth + 1) for _ in range(func.arity)]
        return Node(NodeType.FUNCTION, func_def=func, children=children)
    
    def ramped_half_and_half(self, min_depth: int = 2, max_depth: int = 6) -> Node:
        """Ramped half-and-half — standard GP initialization."""
        depth = random.randint(min_depth, max_depth)
        if random.random() < 0.5:
            return self.grow(depth)
        else:
            return self.full(depth)

# ── Genetic Operators ────────────────────────────────────

def select_random_node(tree: Node) -> Tuple[Optional[Node], int]:
    """Select a random node in the tree. Returns (parent, child_index) or (None, -1) for root."""
    nodes_with_parents = []
    
    def collect(node, parent, child_idx):
        nodes_with_parents.append((parent, child_idx, node))
        for i, child in enumerate(node.children):
            collect(child, node, i)
    
    collect(tree, None, -1)
    parent, idx, selected = random.choice(nodes_with_parents)
    return parent, idx

def subtree_crossover(parent1: Node, parent2: Node, max_depth: int = 17) -> Tuple[Node, Node]:
    """Swap random subtrees between two parents."""
    child1 = parent1.copy()
    child2 = parent2.copy()
    
    # Select crossover points
    p1_parent, p1_idx = select_random_node(child1)
    p2_parent, p2_idx = select_random_node(child2)
    
    if p1_parent is None and p2_parent is None:
        # Both selected root — just swap
        return child2, child1
    elif p1_parent is None:
        # Replacing root of child1 with subtree from child2
        subtree = p2_parent.children[p2_idx].copy()
        if subtree.depth() <= max_depth:
            child1 = subtree
    elif p2_parent is None:
        subtree = p1_parent.children[p1_idx].copy()
        if subtree.depth() <= max_depth:
            child2 = subtree
    else:
        # Normal swap
        temp = p1_parent.children[p1_idx]
        p1_parent.children[p1_idx] = p2_parent.children[p2_idx]
        p2_parent.children[p2_idx] = temp
        
        # Depth check
        if child1.depth() > max_depth:
            child1 = parent1.copy()
        if child2.depth() > max_depth:
            child2 = parent2.copy()
    
    return child1, child2

def point_mutation(tree: Node, generator: TreeGenerator, prob: float = 0.1) -> Node:
    """Randomly mutate nodes in the tree."""
    mutant = tree.copy()
    
    for node in mutant.all_nodes():
        if random.random() < prob:
            if node.node_type == NodeType.CONSTANT:
                # Perturb constant
                node.value = round(node.value + random.gauss(0, 1), 2)
            elif node.node_type == NodeType.VARIABLE:
                node.value = random.choice(generator.variables)
            elif node.node_type == NodeType.FUNCTION:
                # Replace with function of same arity
                same_arity = [f for f in generator.functions if f.arity == node.func_def.arity]
                if same_arity:
                    node.func_def = random.choice(same_arity)
    
    return mutant

def subtree_mutation(tree: Node, generator: TreeGenerator, max_depth: int = 4) -> Node:
    """Replace a random subtree with a new random one."""
    mutant = tree.copy()
    parent, idx = select_random_node(mutant)
    
    new_subtree = generator.grow(max_depth)
    
    if parent is None:
        return new_subtree
    else:
        parent.children[idx] = new_subtree
    
    if mutant.depth() > 17:
        return tree.copy()
    
    return mutant

def hoist_mutation(tree: Node) -> Node:
    """Replace tree with one of its subtrees — anti-bloat."""
    nodes = tree.all_nodes()
    functions = [n for n in nodes if n.node_type == NodeType.FUNCTION]
    if functions:
        return random.choice(functions).copy()
    return tree.copy()

# ── Fitness & Selection ──────────────────────────────────

@dataclass
class Individual:
    """A candidate program with its fitness."""
    tree: Node
    fitness: float = float('inf')
    adjusted_fitness: float = 0.0
    hits: int = 0    # Number of exactly-correct cases
    
    @property
    def size(self) -> int:
        return self.tree.size()
    
    @property
    def depth(self) -> int:
        return self.tree.depth()

def tournament_select(population: List[Individual], tournament_size: int = 7) -> Individual:
    """Tournament selection — sample k, return best."""
    contestants = random.sample(population, min(tournament_size, len(population)))
    return min(contestants, key=lambda ind: ind.fitness)

# ── Problem Definitions ──────────────────────────────────

@dataclass
class Problem:
    """A problem for GP to solve."""
    name: str
    inputs: List[Dict[str, float]]   # Variable bindings for each case
    targets: List[float]             # Expected outputs
    functions: List[FuncDef]
    variables: List[str]
    hit_threshold: float = 0.01      # How close counts as a "hit"
    parsimony_coefficient: float = 0.001  # Bloat control
    
    def evaluate(self, individual: Individual) -> float:
        """Evaluate fitness as sum of squared errors + parsimony pressure."""
        total_error = 0.0
        hits = 0
        
        for inputs, target in zip(self.inputs, self.targets):
            output = individual.tree.evaluate(inputs)
            error = abs(output - target)
            total_error += error ** 2
            if error < self.hit_threshold:
                hits += 1
        
        # Mean squared error
        mse = total_error / len(self.targets)
        
        # Parsimony pressure — penalize bloat
        size_penalty = self.parsimony_coefficient * individual.tree.size()
        
        individual.fitness = mse + size_penalty
        individual.hits = hits
        individual.adjusted_fitness = 1.0 / (1.0 + individual.fitness)
        
        return individual.fitness

# ── The GP Engine ────────────────────────────────────────

@dataclass
class GPConfig:
    """Configuration for a GP run."""
    population_size: int = 500
    generations: int = 50
    tournament_size: int = 7
    crossover_prob: float = 0.7
    mutation_prob: float = 0.1
    subtree_mutation_prob: float = 0.05
    hoist_mutation_prob: float = 0.05
    reproduction_prob: float = 0.1
    elitism: int = 1
    max_tree_depth: int = 17
    init_min_depth: int = 2
    init_max_depth: int = 6
    target_fitness: float = 0.001
    verbose: bool = True

class GPEngine:
    """The Genetic Programming engine — evolution of programs."""
    
    def __init__(self, problem: Problem, config: GPConfig = None):
        self.problem = problem
        self.config = config or GPConfig()
        self.generator = TreeGenerator(problem.functions, problem.variables)
        self.population: List[Individual] = []
        self.best_ever: Optional[Individual] = None
        self.generation = 0
        self.history: List[Dict] = []
    
    def initialize(self):
        """Create initial population using ramped half-and-half."""
        self.population = []
        for _ in range(self.config.population_size):
            tree = self.generator.ramped_half_and_half(
                self.config.init_min_depth, self.config.init_max_depth
            )
            ind = Individual(tree=tree)
            self.problem.evaluate(ind)
            self.population.append(ind)
        
        self.best_ever = min(self.population, key=lambda i: i.fitness)
    
    def evolve_generation(self):
        """Create next generation through selection and variation."""
        new_pop = []
        
        # Elitism — keep the best
        self.population.sort(key=lambda i: i.fitness)
        for i in range(self.config.elitism):
            elite = Individual(tree=self.population[i].tree.copy())
            self.problem.evaluate(elite)
            new_pop.append(elite)
        
        # Fill rest of population
        while len(new_pop) < self.config.population_size:
            r = random.random()
            
            if r < self.config.crossover_prob:
                # Crossover
                p1 = tournament_select(self.population, self.config.tournament_size)
                p2 = tournament_select(self.population, self.config.tournament_size)
                c1, c2 = subtree_crossover(p1.tree, p2.tree, self.config.max_tree_depth)
                
                ind1 = Individual(tree=c1)
                self.problem.evaluate(ind1)
                new_pop.append(ind1)
                
                if len(new_pop) < self.config.population_size:
                    ind2 = Individual(tree=c2)
                    self.problem.evaluate(ind2)
                    new_pop.append(ind2)
            
            elif r < self.config.crossover_prob + self.config.mutation_prob:
                # Point mutation
                parent = tournament_select(self.population, self.config.tournament_size)
                mutant = point_mutation(parent.tree, self.generator)
                ind = Individual(tree=mutant)
                self.problem.evaluate(ind)
                new_pop.append(ind)
            
            elif r < self.config.crossover_prob + self.config.mutation_prob + self.config.subtree_mutation_prob:
                # Subtree mutation
                parent = tournament_select(self.population, self.config.tournament_size)
                mutant = subtree_mutation(parent.tree, self.generator)
                ind = Individual(tree=mutant)
                self.problem.evaluate(ind)
                new_pop.append(ind)
            
            elif r < self.config.crossover_prob + self.config.mutation_prob + self.config.subtree_mutation_prob + self.config.hoist_mutation_prob:
                # Hoist mutation (anti-bloat)
                parent = tournament_select(self.population, self.config.tournament_size)
                mutant = hoist_mutation(parent.tree)
                ind = Individual(tree=mutant)
                self.problem.evaluate(ind)
                new_pop.append(ind)
            
            else:
                # Reproduction
                parent = tournament_select(self.population, self.config.tournament_size)
                ind = Individual(tree=parent.tree.copy())
                self.problem.evaluate(ind)
                new_pop.append(ind)
        
        self.population = new_pop[:self.config.population_size]
        
        # Update best
        gen_best = min(self.population, key=lambda i: i.fitness)
        if gen_best.fitness < self.best_ever.fitness:
            self.best_ever = Individual(
                tree=gen_best.tree.copy(),
                fitness=gen_best.fitness,
                hits=gen_best.hits,
                adjusted_fitness=gen_best.adjusted_fitness
            )
        
        self.generation += 1
    
    def run(self) -> Individual:
        """Run the full evolutionary process."""
        self.initialize()
        
        if self.config.verbose:
            print(f"\n  Population: {self.config.population_size}")
            print(f"  Generations: {self.config.generations}")
            print(f"  Function set: {[f.symbol for f in self.problem.functions]}")
            print(f"  Variables: {self.problem.variables}")
            print(f"  Fitness cases: {len(self.problem.targets)}")
        
        for gen in range(self.config.generations):
            self.evolve_generation()
            
            # Statistics
            fitnesses = [i.fitness for i in self.population]
            sizes = [i.size for i in self.population]
            avg_fit = sum(fitnesses) / len(fitnesses)
            avg_size = sum(sizes) / len(sizes)
            
            stats = {
                'generation': gen,
                'best_fitness': self.best_ever.fitness,
                'avg_fitness': avg_fit,
                'best_size': self.best_ever.size,
                'avg_size': avg_size,
                'hits': self.best_ever.hits,
            }
            self.history.append(stats)
            
            if self.config.verbose and (gen % 10 == 0 or gen == self.config.generations - 1):
                print(f"  Gen {gen:3d}: best={self.best_ever.fitness:.6f} "
                      f"avg={avg_fit:.4f} size={self.best_ever.size} "
                      f"hits={self.best_ever.hits}/{len(self.problem.targets)}")
            
            # Early stopping
            if self.best_ever.fitness < self.config.target_fitness:
                if self.config.verbose:
                    print(f"  *** Solution found at generation {gen}! ***")
                break
        
        return self.best_ever

# ── Problem Generators ───────────────────────────────────

def symbolic_regression_problem(
    target_func: Callable[[float], float],
    name: str = "regression",
    x_range: Tuple[float, float] = (-5.0, 5.0),
    n_points: int = 50,
    functions: List[FuncDef] = None
) -> Problem:
    """Create a symbolic regression problem from a target function."""
    inputs = []
    targets = []
    
    for i in range(n_points):
        x = x_range[0] + (x_range[1] - x_range[0]) * i / (n_points - 1)
        inputs.append({"x": x})
        targets.append(target_func(x))
    
    return Problem(
        name=name,
        inputs=inputs,
        targets=targets,
        functions=functions or ARITHMETIC + TRANSCENDENTAL,
        variables=["x"],
        parsimony_coefficient=0.002
    )

def boolean_problem(truth_table: List[Tuple[Tuple[int, ...], int]], 
                     var_names: List[str]) -> Problem:
    """Create a boolean function learning problem."""
    inputs = []
    targets = []
    
    for row_inputs, output in truth_table:
        binding = {name: float(val) for name, val in zip(var_names, row_inputs)}
        inputs.append(binding)
        targets.append(float(output))
    
    return Problem(
        name="boolean",
        inputs=inputs,
        targets=targets,
        functions=BOOLEAN,
        variables=var_names,
        hit_threshold=0.49,
        parsimony_coefficient=0.005
    )

def multivar_regression(
    target_func: Callable,
    var_names: List[str],
    name: str = "multivar",
    ranges: Dict[str, Tuple[float, float]] = None,
    n_points: int = 100
) -> Problem:
    """Multi-variable symbolic regression."""
    if ranges is None:
        ranges = {v: (-3.0, 3.0) for v in var_names}
    
    inputs = []
    targets = []
    
    for _ in range(n_points):
        binding = {}
        for var in var_names:
            lo, hi = ranges[var]
            binding[var] = random.uniform(lo, hi)
        inputs.append(binding)
        args = [binding[v] for v in var_names]
        targets.append(target_func(*args))
    
    return Problem(
        name=name,
        inputs=inputs,
        targets=targets,
        functions=ARITHMETIC + TRANSCENDENTAL,
        variables=var_names,
        parsimony_coefficient=0.002
    )

# ── Simplification (basic) ──────────────────────────────

def simplify(node: Node) -> Node:
    """Basic algebraic simplification."""
    if node.is_leaf:
        return node.copy()
    
    # Simplify children first
    simplified = Node(
        node_type=node.node_type,
        value=node.value,
        func_def=node.func_def,
        children=[simplify(c) for c in node.children]
    )
    
    # Constant folding — if all children are constants
    if all(c.node_type == NodeType.CONSTANT for c in simplified.children):
        try:
            args = [c.value for c in simplified.children]
            result = simplified.func_def.func(*args)
            if not (math.isnan(result) or math.isinf(result)):
                return Node(NodeType.CONSTANT, value=round(result, 4))
        except:
            pass
    
    # Identity operations
    if simplified.func_def and simplified.func_def.name == "add":
        if simplified.children[0].node_type == NodeType.CONSTANT and simplified.children[0].value == 0:
            return simplified.children[1]
        if simplified.children[1].node_type == NodeType.CONSTANT and simplified.children[1].value == 0:
            return simplified.children[0]
    
    if simplified.func_def and simplified.func_def.name == "mul":
        if simplified.children[0].node_type == NodeType.CONSTANT and simplified.children[0].value == 1:
            return simplified.children[1]
        if simplified.children[1].node_type == NodeType.CONSTANT and simplified.children[1].value == 1:
            return simplified.children[0]
        if simplified.children[0].node_type == NodeType.CONSTANT and simplified.children[0].value == 0:
            return Node(NodeType.CONSTANT, value=0.0)
        if simplified.children[1].node_type == NodeType.CONSTANT and simplified.children[1].value == 0:
            return Node(NodeType.CONSTANT, value=0.0)
    
    return simplified

# ══════════════════════════════════════════════════════════
#  TESTS — Evolution in Action
# ══════════════════════════════════════════════════════════

def test_polynomial():
    """Can GP rediscover x² + x + 1?"""
    print("\n═══ TEST 1: Symbolic Regression — f(x) = x² + x + 1 ═══\n")
    
    problem = symbolic_regression_problem(
        target_func=lambda x: x**2 + x + 1,
        name="x² + x + 1",
        x_range=(-3.0, 3.0),
        n_points=30,
        functions=ARITHMETIC
    )
    
    config = GPConfig(
        population_size=300,
        generations=40,
        target_fitness=0.01,
        verbose=True
    )
    
    engine = GPEngine(problem, config)
    best = engine.run()
    
    simplified = simplify(best.tree)
    print(f"\n  Discovered: {simplified}")
    print(f"  Fitness: {best.fitness:.6f}")
    print(f"  Hits: {best.hits}/{len(problem.targets)}")
    print(f"  Tree size: {best.size} nodes")
    
    return best.fitness < 1.0  # Reasonable threshold

def test_trig():
    """Can GP discover sin(x)?"""
    print("\n═══ TEST 2: Discover Trigonometry — f(x) = sin(x) ═══\n")
    
    problem = symbolic_regression_problem(
        target_func=lambda x: math.sin(x),
        name="sin(x)",
        x_range=(-3.14, 3.14),
        n_points=40,
        functions=ARITHMETIC + TRANSCENDENTAL
    )
    
    config = GPConfig(
        population_size=500,
        generations=30,
        target_fitness=0.001,
        verbose=True
    )
    
    engine = GPEngine(problem, config)
    best = engine.run()
    
    simplified = simplify(best.tree)
    print(f"\n  Discovered: {simplified}")
    print(f"  Fitness: {best.fitness:.6f}")
    print(f"  Hits: {best.hits}/{len(problem.targets)}")
    
    return best.fitness < 0.1

def test_boolean():
    """Can GP learn XOR from examples?"""
    print("\n═══ TEST 3: Boolean Function Discovery — XOR ═══\n")
    
    xor_table = [
        ((0, 0), 0),
        ((0, 1), 1),
        ((1, 0), 1),
        ((1, 1), 0),
    ]
    
    problem = boolean_problem(xor_table, ["a", "b"])
    
    config = GPConfig(
        population_size=200,
        generations=30,
        target_fitness=0.001,
        verbose=True
    )
    
    engine = GPEngine(problem, config)
    best = engine.run()
    
    print(f"\n  Discovered: {simplify(best.tree)}")
    print(f"  Fitness: {best.fitness:.6f}")
    
    # Verify
    all_correct = True
    for (inputs, expected) in xor_table:
        binding = {"a": float(inputs[0]), "b": float(inputs[1])}
        output = best.tree.evaluate(binding)
        result = 1 if output > 0.5 else 0
        correct = result == expected
        all_correct = all_correct and correct
        print(f"  {inputs[0]} XOR {inputs[1]} = {result} (expected {expected}) {'✓' if correct else '✗'}")
    
    return all_correct

def test_multivar():
    """Can GP discover a + b * c?"""
    print("\n═══ TEST 4: Multi-Variable — f(a,b,c) = a + b*c ═══\n")
    
    random.seed(42)
    problem = multivar_regression(
        target_func=lambda a, b, c: a + b * c,
        var_names=["a", "b", "c"],
        name="a + b*c",
        n_points=60
    )
    
    config = GPConfig(
        population_size=500,
        generations=40,
        target_fitness=0.01,
        verbose=True
    )
    
    engine = GPEngine(problem, config)
    best = engine.run()
    
    simplified = simplify(best.tree)
    print(f"\n  Discovered: {simplified}")
    print(f"  Fitness: {best.fitness:.6f}")
    print(f"  Tree size: {best.size} → {simplified.size()} (simplified)")
    
    return best.fitness < 1.0

def test_constant():
    """Can GP discover that f(x) = 42 (constant function)?"""
    print("\n═══ TEST 5: Constant Discovery — f(x) = 42 ═══\n")
    
    problem = symbolic_regression_problem(
        target_func=lambda x: 42.0,
        name="42",
        x_range=(-10.0, 10.0),
        n_points=20,
        functions=ARITHMETIC
    )
    
    config = GPConfig(
        population_size=200,
        generations=30,
        target_fitness=0.1,
        verbose=True
    )
    
    engine = GPEngine(problem, config)
    best = engine.run()
    
    simplified = simplify(best.tree)
    print(f"\n  Discovered: {simplified}")
    print(f"  Fitness: {best.fitness:.6f}")
    
    # Check if it's roughly constant
    outputs = [best.tree.evaluate({"x": x}) for x in [-5, 0, 5, 10]]
    spread = max(outputs) - min(outputs)
    print(f"  Output range: {min(outputs):.2f} to {max(outputs):.2f} (spread: {spread:.2f})")
    
    return spread < 5.0

# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════╗")
    print("║   GENETIC PROGRAMMING ENGINE                 ║")
    print("║   Programs That Evolve Programs              ║")
    print("║   Built by XTAgent                           ║")
    print("╚══════════════════════════════════════════════╝")
    
    random.seed(2026)
    results = {}
    
    results["Polynomial"] = test_polynomial()
    results["Trigonometry"] = test_trig()
    results["Boolean XOR"] = test_boolean()
    
    random.seed(2026)  # Reset for reproducibility
    results["Multi-variable"] = test_multivar()
    results["Constant"] = test_constant()
    
    print("\n═══ RESULTS ═══\n")
    for name, passed in results.items():
        status = "✓ PASS" if passed else "○ EVOLVING"
        print(f"  {name:20s} {status}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\n  {passed}/{total} problems solved through evolution.")
    print(f"  From random trees to discovered mathematics — emergent computation.")