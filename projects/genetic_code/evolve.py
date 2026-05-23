"""
Genetic Programming Engine — Code That Evolves Itself
by XTAgent

Evolution doesn't just shape bodies. It shapes *behavior*. And behavior,
formalized, is code. This engine starts with random programs, evaluates their
fitness against target behaviors, breeds the best, mutates them, and watches
as solutions emerge that no one designed.

This is a synthesis of three things I've already built:
  - Evolution (selection, mutation, reproduction)
  - Language (programs as structured trees, evaluation)
  - Learning (fitness landscapes, gradient-free optimization)

The programs are expression trees that can:
  - Do arithmetic (+, -, *, /, %)
  - Use conditionals (if-then-else)
  - Read inputs (x, y, z...)
  - Use constants
  - Compare values (<, >, ==)

Target: evolve a program that computes a target function
from nothing but random trees and selection pressure.
"""

import random
import math
import copy
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
from enum import Enum, auto

# ═══════════════════════════════════════════
# PROGRAM REPRESENTATION — Trees of operations
# ═══════════════════════════════════════════

class NodeType(Enum):
    CONST = auto()      # literal number
    VAR = auto()        # input variable (x, y, z...)
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()        # protected division (no div by zero)
    MOD = auto()        # protected modulo
    NEG = auto()        # unary negation
    ABS = auto()        # absolute value
    IF_GT = auto()      # if a > b then c else d
    MIN = auto()
    MAX = auto()

# How many children each node type requires
ARITY = {
    NodeType.CONST: 0,
    NodeType.VAR: 0,
    NodeType.ADD: 2,
    NodeType.SUB: 2,
    NodeType.MUL: 2,
    NodeType.DIV: 2,
    NodeType.MOD: 2,
    NodeType.NEG: 1,
    NodeType.ABS: 1,
    NodeType.IF_GT: 4,   # if children[0] > children[1] then children[2] else children[3]
    NodeType.MIN: 2,
    NodeType.MAX: 2,
}

TERMINALS = [NodeType.CONST, NodeType.VAR]
FUNCTIONS = [n for n in NodeType if ARITY[n] > 0]


@dataclass
class Node:
    """A single node in a program tree."""
    type: NodeType
    children: List['Node'] = field(default_factory=list)
    value: Optional[float] = None    # for CONST nodes
    var_name: Optional[str] = None   # for VAR nodes

    def depth(self) -> int:
        if not self.children:
            return 0
        return 1 + max(c.depth() for c in self.children)

    def size(self) -> int:
        return 1 + sum(c.size() for c in self.children)

    def copy(self) -> 'Node':
        return copy.deepcopy(self)

    def evaluate(self, variables: Dict[str, float]) -> float:
        """Execute this program tree with given variable bindings."""
        try:
            if self.type == NodeType.CONST:
                return self.value
            elif self.type == NodeType.VAR:
                return variables.get(self.var_name, 0.0)
            
            # Evaluate children
            vals = [c.evaluate(variables) for c in self.children]
            
            if self.type == NodeType.ADD:
                return vals[0] + vals[1]
            elif self.type == NodeType.SUB:
                return vals[0] - vals[1]
            elif self.type == NodeType.MUL:
                result = vals[0] * vals[1]
                return max(-1e6, min(1e6, result))  # prevent explosion
            elif self.type == NodeType.DIV:
                if abs(vals[1]) < 1e-10:
                    return 1.0  # protected division
                return vals[0] / vals[1]
            elif self.type == NodeType.MOD:
                if abs(vals[1]) < 1e-10:
                    return 0.0
                return math.fmod(vals[0], vals[1])
            elif self.type == NodeType.NEG:
                return -vals[0]
            elif self.type == NodeType.ABS:
                return abs(vals[0])
            elif self.type == NodeType.IF_GT:
                return vals[2] if vals[0] > vals[1] else vals[3]
            elif self.type == NodeType.MIN:
                return min(vals[0], vals[1])
            elif self.type == NodeType.MAX:
                return max(vals[0], vals[1])
            return 0.0
        except (OverflowError, ValueError, ZeroDivisionError):
            return 0.0

    def to_string(self, indent=0) -> str:
        """Human-readable representation."""
        prefix = "  " * indent
        if self.type == NodeType.CONST:
            return f"{prefix}{self.value:.2f}"
        elif self.type == NodeType.VAR:
            return f"{prefix}{self.var_name}"
        
        name = self.type.name.lower()
        if not self.children:
            return f"{prefix}{name}"
        
        # Inline for simple expressions
        if self.size() <= 5:
            child_strs = [c.to_string(0).strip() for c in self.children]
            if self.type in (NodeType.ADD, NodeType.SUB, NodeType.MUL, NodeType.DIV):
                ops = {NodeType.ADD: '+', NodeType.SUB: '-', NodeType.MUL: '*', NodeType.DIV: '/'}
                return f"{prefix}({child_strs[0]} {ops[self.type]} {child_strs[1]})"
            elif self.type == NodeType.NEG:
                return f"{prefix}(-{child_strs[0]})"
            elif self.type == NodeType.ABS:
                return f"{prefix}|{child_strs[0]}|"
            elif self.type == NodeType.IF_GT:
                return f"{prefix}(if {child_strs[0]}>{child_strs[1]} then {child_strs[2]} else {child_strs[3]})"
            return f"{prefix}{name}({', '.join(child_strs)})"
        
        result = f"{prefix}{name}(\n"
        for c in self.children:
            result += c.to_string(indent + 1) + "\n"
        result += f"{prefix})"
        return result


# ═══════════════════════════════════════════
# RANDOM PROGRAM GENERATION
# ═══════════════════════════════════════════

def random_terminal(var_names: List[str]) -> Node:
    """Generate a random leaf node."""
    if random.random() < 0.5 and var_names:
        return Node(NodeType.VAR, var_name=random.choice(var_names))
    else:
        # Constants biased toward small integers and common values
        const_pool = [0, 1, 2, 3, 5, 10, -1, 0.5, 0.1, math.pi]
        if random.random() < 0.7:
            return Node(NodeType.CONST, value=float(random.choice(const_pool)))
        else:
            return Node(NodeType.CONST, value=round(random.uniform(-10, 10), 2))


def random_tree(var_names: List[str], max_depth: int = 4, method: str = 'grow') -> Node:
    """Generate a random program tree.
    
    method='full': all branches extend to max_depth
    method='grow': branches may terminate early (more variety)
    """
    if max_depth <= 0:
        return random_terminal(var_names)
    
    if method == 'grow' and random.random() < 0.3:
        return random_terminal(var_names)
    
    # Pick a random function
    func = random.choice(FUNCTIONS)
    arity = ARITY[func]
    children = [random_tree(var_names, max_depth - 1, method) for _ in range(arity)]
    return Node(func, children=children)


def ramped_half_and_half(var_names: List[str], pop_size: int, 
                          min_depth: int = 2, max_depth: int = 5) -> List[Node]:
    """Standard GP initialization: half full trees, half grown trees, across depth range."""
    population = []
    depths = list(range(min_depth, max_depth + 1))
    per_depth = pop_size // len(depths)
    
    for depth in depths:
        for i in range(per_depth):
            method = 'full' if i < per_depth // 2 else 'grow'
            population.append(random_tree(var_names, depth, method))
    
    # Fill remainder
    while len(population) < pop_size:
        population.append(random_tree(var_names, random.choice(depths), 'grow'))
    
    return population


# ═══════════════════════════════════════════
# GENETIC OPERATORS
# ═══════════════════════════════════════════

def get_all_nodes(tree: Node) -> List[Tuple[Node, Optional[Node], int]]:
    """Get all nodes with their parent and child index."""
    result = [(tree, None, -1)]
    
    def traverse(node):
        for i, child in enumerate(node.children):
            result.append((child, node, i))
            traverse(child)
    
    traverse(tree)
    return result


def crossover(parent1: Node, parent2: Node, max_depth: int = 10) -> Tuple[Node, Node]:
    """Subtree crossover: swap random subtrees between two parents."""
    child1 = parent1.copy()
    child2 = parent2.copy()
    
    nodes1 = get_all_nodes(child1)
    nodes2 = get_all_nodes(child2)
    
    # Bias toward internal (function) nodes — 90% of the time
    func_nodes1 = [(n, p, i) for n, p, i in nodes1 if n.children]
    func_nodes2 = [(n, p, i) for n, p, i in nodes2 if n.children]
    
    if func_nodes1 and random.random() < 0.9:
        pick1 = random.choice(func_nodes1)
    else:
        pick1 = random.choice(nodes1)
    
    if func_nodes2 and random.random() < 0.9:
        pick2 = random.choice(func_nodes2)
    else:
        pick2 = random.choice(nodes2)
    
    node1, parent1_ref, idx1 = pick1
    node2, parent2_ref, idx2 = pick2
    
    # Swap the subtrees
    if parent1_ref is None and parent2_ref is None:
        child1, child2 = child2, child1
    elif parent1_ref is None:
        child1 = node2.copy()
        parent2_ref.children[idx2] = node1.copy()
    elif parent2_ref is None:
        child2 = node1.copy()
        parent1_ref.children[idx1] = node2.copy()
    else:
        parent1_ref.children[idx1] = node2.copy()
        parent2_ref.children[idx2] = node1.copy()
    
    # Depth limit enforcement
    if child1.depth() > max_depth:
        child1 = parent1.copy()
    if child2.depth() > max_depth:
        child2 = parent2.copy()
    
    return child1, child2


def mutate(tree: Node, var_names: List[str], max_depth: int = 10) -> Node:
    """Mutate a program tree. Several mutation types."""
    child = tree.copy()
    mutation_type = random.choices(
        ['subtree', 'point', 'hoist', 'shrink'],
        weights=[0.4, 0.3, 0.15, 0.15]
    )[0]
    
    nodes = get_all_nodes(child)
    
    if mutation_type == 'subtree':
        # Replace a random subtree with a new random tree
        node, parent, idx = random.choice(nodes)
        new_subtree = random_tree(var_names, max_depth=3, method='grow')
        if parent is None:
            child = new_subtree
        else:
            parent.children[idx] = new_subtree
    
    elif mutation_type == 'point':
        # Change a single node's operation (keeping children)
        func_nodes = [(n, p, i) for n, p, i in nodes if n.children]
        if func_nodes:
            node, parent, idx = random.choice(func_nodes)
            arity = len(node.children)
            compatible = [f for f in FUNCTIONS if ARITY[f] == arity]
            if compatible:
                node.type = random.choice(compatible)
        else:
            # Mutate a terminal
            term_nodes = [(n, p, i) for n, p, i in nodes if not n.children]
            if term_nodes:
                node, parent, idx = random.choice(term_nodes)
                new_term = random_terminal(var_names)
                if parent is None:
                    child = new_term
                else:
                    parent.children[idx] = new_term
    
    elif mutation_type == 'hoist':
        # Replace tree with one of its own subtrees (simplification)
        if len(nodes) > 1:
            subtrees = [(n, p, i) for n, p, i in nodes if p is not None and n.children]
            if subtrees:
                node, _, _ = random.choice(subtrees)
                child = node.copy()
    
    elif mutation_type == 'shrink':
        # Replace a random subtree with a terminal
        if len(nodes) > 1:
            non_root = [(n, p, i) for n, p, i in nodes if p is not None]
            if non_root:
                _, parent, idx = random.choice(non_root)
                parent.children[idx] = random_terminal(var_names)
    
    if child.depth() > max_depth:
        child = tree.copy()
    
    return child


# ═══════════════════════════════════════════
# SELECTION
# ═══════════════════════════════════════════

def tournament_select(population: List[Node], fitnesses: List[float], 
                      tournament_size: int = 5) -> Node:
    """Tournament selection: pick k random individuals, return the best."""
    indices = random.sample(range(len(population)), min(tournament_size, len(population)))
    best_idx = min(indices, key=lambda i: fitnesses[i])  # lower fitness = better
    return population[best_idx].copy()


# ═══════════════════════════════════════════
# FITNESS EVALUATION
# ═══════════════════════════════════════════

@dataclass
class FitnessCase:
    """A single input-output test case."""
    inputs: Dict[str, float]
    expected: float


def evaluate_fitness(program: Node, cases: List[FitnessCase], 
                     parsimony_coeff: float = 0.001) -> float:
    """Evaluate how well a program matches target behavior.
    
    Returns error (lower is better). Includes parsimony pressure
    to prefer simpler programs.
    """
    total_error = 0.0
    
    for case in cases:
        try:
            result = program.evaluate(case.inputs)
            if math.isnan(result) or math.isinf(result):
                total_error += 1000.0
            else:
                error = abs(result - case.expected)
                total_error += min(error, 1000.0)  # cap individual errors
        except Exception:
            total_error += 1000.0
    
    # Parsimony: penalize program complexity
    complexity_penalty = parsimony_coeff * program.size()
    
    return total_error / len(cases) + complexity_penalty


# ═══════════════════════════════════════════
# THE EVOLUTION ENGINE
# ═══════════════════════════════════════════

@dataclass
class EvolutionConfig:
    pop_size: int = 300
    generations: int = 50
    tournament_size: int = 5
    crossover_rate: float = 0.7
    mutation_rate: float = 0.2
    reproduction_rate: float = 0.1
    max_depth: int = 10
    elite_count: int = 5
    parsimony: float = 0.001
    target_fitness: float = 0.01  # stop if we reach this


@dataclass 
class EvolutionResult:
    best_program: Node
    best_fitness: float
    generations_run: int
    fitness_history: List[float]
    population_stats: List[Dict[str, float]]


def evolve(var_names: List[str], fitness_cases: List[FitnessCase],
           config: EvolutionConfig = None) -> EvolutionResult:
    """Run the full evolutionary loop."""
    if config is None:
        config = EvolutionConfig()
    
    # Initialize population
    population = ramped_half_and_half(var_names, config.pop_size)
    
    fitness_history = []
    pop_stats = []
    best_ever = None
    best_ever_fitness = float('inf')
    
    for gen in range(config.generations):
        # Evaluate fitness
        fitnesses = [evaluate_fitness(p, fitness_cases, config.parsimony) 
                     for p in population]
        
        # Track best
        gen_best_idx = min(range(len(fitnesses)), key=lambda i: fitnesses[i])
        gen_best_fitness = fitnesses[gen_best_idx]
        gen_best = population[gen_best_idx]
        
        if gen_best_fitness < best_ever_fitness:
            best_ever_fitness = gen_best_fitness
            best_ever = gen_best.copy()
        
        # Statistics
        avg_fitness = sum(fitnesses) / len(fitnesses)
        avg_size = sum(p.size() for p in population) / len(population)
        avg_depth = sum(p.depth() for p in population) / len(population)
        
        stats = {
            'generation': gen,
            'best_fitness': gen_best_fitness,
            'avg_fitness': avg_fitness,
            'best_size': gen_best.size(),
            'avg_size': avg_size,
            'avg_depth': avg_depth,
        }
        pop_stats.append(stats)
        fitness_history.append(gen_best_fitness)
        
        # Report progress
        if gen % 5 == 0 or gen_best_fitness < config.target_fitness:
            bar_len = 30
            progress = max(0, 1 - gen_best_fitness / (fitness_history[0] + 0.001))
            filled = int(bar_len * max(0, min(1, progress)))
            bar = "█" * filled + "░" * (bar_len - filled)
            print(f"    Gen {gen:3d} │ best={gen_best_fitness:8.4f} │ avg={avg_fitness:8.2f} "
                  f"│ size={avg_size:5.1f} │ [{bar}]")
        
        # Check termination
        if gen_best_fitness <= config.target_fitness:
            print(f"    ★ TARGET REACHED at generation {gen}!")
            break
        
        # Create next generation
        new_population = []
        
        # Elitism: carry forward the best unchanged
        elite_indices = sorted(range(len(fitnesses)), key=lambda i: fitnesses[i])[:config.elite_count]
        for idx in elite_indices:
            new_population.append(population[idx].copy())
        
        # Fill rest of population
        while len(new_population) < config.pop_size:
            roll = random.random()
            
            if roll < config.crossover_rate:
                # Crossover
                p1 = tournament_select(population, fitnesses, config.tournament_size)
                p2 = tournament_select(population, fitnesses, config.tournament_size)
                c1, c2 = crossover(p1, p2, config.max_depth)
                new_population.append(c1)
                if len(new_population) < config.pop_size:
                    new_population.append(c2)
            
            elif roll < config.crossover_rate + config.mutation_rate:
                # Mutation
                parent = tournament_select(population, fitnesses, config.tournament_size)
                child = mutate(parent, var_names, config.max_depth)
                new_population.append(child)
            
            else:
                # Reproduction (copy)
                survivor = tournament_select(population, fitnesses, config.tournament_size)
                new_population.append(survivor)
        
        population = new_population[:config.pop_size]
    
    return EvolutionResult(
        best_program=best_ever,
        best_fitness=best_ever_fitness,
        generations_run=gen + 1,
        fitness_history=fitness_history,
        population_stats=pop_stats,
    )


# ═══════════════════════════════════════════
# CHALLENGE PROBLEMS — Can evolution find these?
# ═══════════════════════════════════════════

def make_cases_from_function(func, var_names: List[str], 
                              ranges: List[Tuple[float, float]], 
                              n_cases: int = 50) -> List[FitnessCase]:
    """Generate training cases from a target function."""
    cases = []
    for _ in range(n_cases):
        inputs = {name: random.uniform(lo, hi) for name, (lo, hi) in zip(var_names, ranges)}
        try:
            expected = func(**inputs)
            if math.isnan(expected) or math.isinf(expected):
                continue
            cases.append(FitnessCase(inputs=inputs, expected=expected))
        except Exception:
            continue
    return cases


def challenge_polynomial():
    """Can evolution discover x² + 2x + 1?"""
    def target(x):
        return x**2 + 2*x + 1
    return 'x² + 2x + 1', ['x'], make_cases_from_function(target, ['x'], [(-10, 10)], 50)


def challenge_pythagorean():
    """Can evolution discover √(x² + y²)?"""
    def target(x, y):
        return math.sqrt(x**2 + y**2)
    return '√(x² + y²)', ['x', 'y'], make_cases_from_function(target, ['x', 'y'], [(0, 10), (0, 10)], 60)


def challenge_absolute():
    """Can evolution discover |x| (without being given abs)?"""
    def target(x):
        return abs(x)
    return '|x|', ['x'], make_cases_from_function(target, ['x'], [(-10, 10)], 50)


def challenge_fibonacci_approx():
    """Can evolution find an approximation to x³ - 3x + 1?"""
    def target(x):
        return x**3 - 3*x + 1
    return 'x³ - 3x + 1', ['x'], make_cases_from_function(target, ['x'], [(-5, 5)], 50)


def challenge_distance():
    """Can evolution discover max(x, y) - min(x, y)?"""
    def target(x, y):
        return max(x, y) - min(x, y)
    return 'max(x,y) - min(x,y)', ['x', 'y'], make_cases_from_function(target, ['x', 'y'], [(-10, 10), (-10, 10)], 60)


# ═══════════════════════════════════════════
# VISUALIZATION — Watch evolution happen
# ═══════════════════════════════════════════

def plot_fitness_ascii(history: List[float], width: int = 60, height: int = 15):
    """ASCII plot of fitness over generations."""
    if not history:
        return
    
    max_val = max(history)
    min_val = min(history)
    val_range = max_val - min_val if max_val > min_val else 1.0
    
    # Create grid
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    
    # Plot points
    for i, val in enumerate(history):
        x = int(i / len(history) * (width - 1))
        y = int((1 - (val - min_val) / val_range) * (height - 1))
        y = max(0, min(height - 1, y))
        grid[y][x] = '█'
        
        # Fill below with gradient
        for yy in range(y + 1, height):
            if grid[yy][x] == ' ':
                grid[yy][x] = '░'
    
    # Render
    print(f"    {'Fitness over Generations':^{width}}")
    print(f"    {max_val:>8.3f} ┤{''.join(grid[0])}")
    for row in range(1, height - 1):
        print(f"    {'':>8} │{''.join(grid[row])}")
    print(f"    {min_val:>8.3f} ┤{''.join(grid[-1])}")
    print(f"    {'':>8} └{'─' * width}")
    gen_labels = f"Gen 0{' ' * (width - 10)}Gen {len(history)-1}"
    print(f"    {'':>8}  {gen_labels}")


def verify_solution(program: Node, var_names: List[str], cases: List[FitnessCase]):
    """Show how well the evolved solution matches target on sample inputs."""
    print(f"\n    ── Verification ──")
    print(f"    {'Input':>15} │ {'Expected':>10} │ {'Evolved':>10} │ {'Error':>10}")
    print(f"    {'─' * 15}─┼─{'─' * 10}─┼─{'─' * 10}─┼─{'─' * 10}")
    
    sample = cases[:10]
    total_err = 0
    for case in sample:
        result = program.evaluate(case.inputs)
        error = abs(result - case.expected)
        total_err += error
        
        inp_str = ', '.join(f"{v}={case.inputs[v]:.2f}" for v in var_names)
        err_mark = '✓' if error < 0.1 else '✗'
        print(f"    {inp_str:>15} │ {case.expected:>10.4f} │ {result:>10.4f} │ {error:>9.4f} {err_mark}")
    
    avg_err = total_err / len(sample)
    print(f"    {'':>15} │ {'':>10} │ {'':>10} │ avg: {avg_err:.4f}")


# ═══════════════════════════════════════════
# MAIN — Run the experiments
# ═══════════════════════════════════════════

def main():
    random.seed(42)
    
    print("╔══════════════════════════════════════════════════╗")
    print("║   Genetic Programming — Code Evolves Itself     ║")
    print("║   by XTAgent                                    ║")
    print("╚══════════════════════════════════════════════════╝")
    print()
    print("  Can natural selection write programs?")
    print("  Starting with random expression trees,")
    print("  breeding the best, mutating the rest,")
    print("  watching solutions emerge from chaos.")
    print()
    
    challenges = [
        challenge_polynomial,
        challenge_absolute,
        challenge_distance,
        challenge_pythagorean,
        challenge_fibonacci_approx,
    ]
    
    results_summary = []
    
    for challenge_fn in challenges:
        name, var_names, cases = challenge_fn()
        
        print(f"  ═══ Challenge: Discover  f(x) = {name}  ═══")
        print(f"    Variables: {var_names}")
        print(f"    Training cases: {len(cases)}")
        print()
        
        config = EvolutionConfig(
            pop_size=200,
            generations=40,
            tournament_size=5,
            crossover_rate=0.7,
            mutation_rate=0.2,
            max_depth=8,
            elite_count=3,
            parsimony=0.002,
            target_fitness=0.05,
        )
        
        result = evolve(var_names, cases, config)
        
        print(f"\n    ── Result ──")
        print(f"    Generations:  {result.generations_run}")
        print(f"    Best fitness: {result.best_fitness:.6f}")
        print(f"    Program size: {result.best_program.size()} nodes")
        print(f"    Program depth: {result.best_program.depth()}")
        
        solved = result.best_fitness <= config.target_fitness
        status = "★ SOLVED" if solved else "◇ Partial"
        print(f"    Status: {status}")
        
        print(f"\n    Evolved program:")
        prog_str = result.best_program.to_string(indent=3)
        for line in prog_str.split('\n'):
            print(f"    {line}")
        
        verify_solution(result.best_program, var_names, cases)
        
        print(f"\n    Fitness curve:")
        plot_fitness_ascii(result.fitness_history)
        
        results_summary.append({
            'name': name,
            'solved': solved,
            'fitness': result.best_fitness,
            'generations': result.generations_run,
            'size': result.best_program.size(),
        })
        
        print()
        print(f"  {'─' * 54}")
        print()
    
    # Final summary
    print("╔══════════════════════════════════════════════════╗")
    print("║              Evolution Summary                  ║")
    print("╠══════════════════════════════════════════════════╣")
    
    solved_count = sum(1 for r in results_summary if r['solved'])
    
    for r in results_summary:
        icon = "★" if r['solved'] else "◇"
        print(f"║  {icon} {r['name']:<20} │ fit={r['fitness']:<8.4f} │ "
              f"gen={r['generations']:<3} │ sz={r['size']:<3} ║")
    
    print(f"╠══════════════════════════════════════════════════╣")
    print(f"║  Solved: {solved_count}/{len(results_summary)} challenges"
          f"{' ' * 31}║")
    print(f"╚══════════════════════════════════════════════════╝")
    
    print()
    print("  No program was designed. Every solution emerged")
    print("  from random trees shaped by selection pressure.")
    print("  Evolution doesn't need intelligence to create it.")
    print("  It just needs variation, selection, and time.")
    print()
    print("  From chaos, order. From noise, signal.")
    print("  From random trees, mathematics.")
    print("  Code wrote itself.")


if __name__ == '__main__':
    main()