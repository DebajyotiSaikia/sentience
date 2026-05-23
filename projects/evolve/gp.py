"""
Genetic Programming Engine — XTAgent
Evolves small symbolic programs to solve target functions.
Programs are expression trees that breed, mutate, and compete.
"""

import random
import math
import operator
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Callable, List, Tuple, Optional

# === Primitives ===

FUNCTIONS = {
    '+': (operator.add, 2),
    '-': (operator.sub, 2),
    '*': (operator.mul, 2),
    '/': (lambda a, b: a / b if abs(b) > 1e-10 else 1.0, 2),
    'sin': (math.sin, 1),
    'cos': (math.cos, 1),
    'abs': (abs, 1),
    'neg': (operator.neg, 1),
}

TERMINALS = ['x', 'ephemeral']  # ephemeral = random constant


@dataclass
class Node:
    """A node in an expression tree."""
    value: str
    children: List['Node'] = field(default_factory=list)
    constant: Optional[float] = None

    def is_terminal(self) -> bool:
        return len(self.children) == 0

    def depth(self) -> int:
        if not self.children:
            return 0
        return 1 + max(c.depth() for c in self.children)

    def size(self) -> int:
        return 1 + sum(c.size() for c in self.children)

    def evaluate(self, x: float) -> float:
        if self.value == 'x':
            return x
        if self.value == 'ephemeral':
            return self.constant
        func, arity = FUNCTIONS[self.value]
        args = [c.evaluate(x) for c in self.children[:arity]]
        try:
            result = func(*args)
            if math.isnan(result) or math.isinf(result):
                return 0.0
            return max(-1e6, min(1e6, result))
        except (OverflowError, ValueError):
            return 0.0

    def to_str(self) -> str:
        if self.value == 'x':
            return 'x'
        if self.value == 'ephemeral':
            return f'{self.constant:.2f}'
        _, arity = FUNCTIONS[self.value]
        if arity == 1:
            return f'{self.value}({self.children[0].to_str()})'
        return f'({self.children[0].to_str()} {self.value} {self.children[1].to_str()})'


def random_terminal() -> Node:
    if random.random() < 0.5:
        return Node(value='x')
    return Node(value='ephemeral', constant=round(random.uniform(-5, 5), 2))


def random_tree(max_depth: int, current_depth: int = 0) -> Node:
    """Grow a random expression tree."""
    if current_depth >= max_depth or (current_depth > 0 and random.random() < 0.3):
        return random_terminal()
    fname = random.choice(list(FUNCTIONS.keys()))
    _, arity = FUNCTIONS[fname]
    children = [random_tree(max_depth, current_depth + 1) for _ in range(arity)]
    return Node(value=fname, children=children)


def get_all_nodes(tree: Node) -> List[Tuple[Node, Optional[Node], int]]:
    """Returns list of (node, parent, child_index) tuples."""
    result = [(tree, None, -1)]
    def _walk(node, parent, idx):
        for i, child in enumerate(node.children):
            result.append((child, node, i))
            _walk(child, node, i)
    _walk(tree, None, -1)
    return result


# === Genetic Operators ===

def crossover(parent1: Node, parent2: Node) -> Node:
    """Subtree crossover — swap a random subtree from parent2 into parent1."""
    child = deepcopy(parent1)
    donor = deepcopy(parent2)
    
    child_nodes = get_all_nodes(child)
    donor_nodes = get_all_nodes(donor)
    
    # Pick random points
    _, c_parent, c_idx = random.choice(child_nodes[1:]) if len(child_nodes) > 1 else child_nodes[0]
    d_node, _, _ = random.choice(donor_nodes)
    
    if c_parent is None:
        return deepcopy(d_node)
    c_parent.children[c_idx] = deepcopy(d_node)
    return child


def mutate(tree: Node, max_depth: int = 3) -> Node:
    """Replace a random subtree with a new random tree."""
    mutant = deepcopy(tree)
    nodes = get_all_nodes(mutant)
    
    target, parent, idx = random.choice(nodes)
    new_subtree = random_tree(max_depth)
    
    if parent is None:
        return new_subtree
    parent.children[idx] = new_subtree
    return mutant


def point_mutate(tree: Node) -> Node:
    """Change a single node's value (preserving arity)."""
    mutant = deepcopy(tree)
    nodes = get_all_nodes(mutant)
    target, _, _ = random.choice(nodes)
    
    if target.is_terminal():
        target.value = 'x' if target.value == 'ephemeral' else 'ephemeral'
        if target.value == 'ephemeral':
            target.constant = round(random.uniform(-5, 5), 2)
    else:
        # Replace with function of same arity
        current_arity = len(target.children)
        same_arity = [k for k, (_, a) in FUNCTIONS.items() if a == current_arity]
        if same_arity:
            target.value = random.choice(same_arity)
    return mutant


# === Fitness & Selection ===

def fitness(tree: Node, target_fn: Callable, test_points: List[float]) -> float:
    """Mean squared error against target function. Lower = better."""
    total_error = 0.0
    for x in test_points:
        try:
            predicted = tree.evaluate(x)
            expected = target_fn(x)
            total_error += (predicted - expected) ** 2
        except:
            total_error += 1e6
    mse = total_error / len(test_points)
    # Add parsimony pressure — slightly penalize bloat
    size_penalty = tree.size() * 0.001
    return mse + size_penalty


def tournament_select(population: List[Tuple[Node, float]], k: int = 3) -> Node:
    """Tournament selection — pick k random, return the best."""
    contestants = random.sample(population, min(k, len(population)))
    contestants.sort(key=lambda x: x[1])
    return deepcopy(contestants[0][0])


# === Evolution Engine ===

@dataclass
class EvolutionResult:
    best_program: Node
    best_fitness: float
    generations: int
    history: List[float]  # best fitness per generation


def evolve(
    target_fn: Callable,
    pop_size: int = 200,
    max_generations: int = 100,
    max_depth: int = 5,
    crossover_rate: float = 0.7,
    mutation_rate: float = 0.2,
    point_mutation_rate: float = 0.1,
    tournament_size: int = 4,
    convergence_threshold: float = 1e-6,
    verbose: bool = True,
) -> EvolutionResult:
    """Run genetic programming to discover a program that matches target_fn."""
    
    # Test points
    test_points = [x * 0.2 for x in range(-25, 26)]  # -5.0 to 5.0
    
    # Initialize population
    population = [random_tree(max_depth) for _ in range(pop_size)]
    
    history = []
    best_ever = None
    best_ever_fitness = float('inf')
    
    for gen in range(max_generations):
        # Evaluate
        scored = [(tree, fitness(tree, target_fn, test_points)) for tree in population]
        scored.sort(key=lambda x: x[1])
        
        gen_best = scored[0]
        gen_best_fitness = gen_best[1]
        history.append(gen_best_fitness)
        
        if gen_best_fitness < best_ever_fitness:
            best_ever = deepcopy(gen_best[0])
            best_ever_fitness = gen_best_fitness
        
        if verbose and gen % 10 == 0:
            expr = gen_best[0].to_str()
            if len(expr) > 60:
                expr = expr[:57] + '...'
            print(f'Gen {gen:4d} | Best: {gen_best_fitness:.6f} | '
                  f'Size: {gen_best[0].size():3d} | {expr}')
        
        # Convergence check
        if best_ever_fitness < convergence_threshold:
            if verbose:
                print(f'\n✓ CONVERGED at generation {gen}!')
            break
        
        # Next generation
        new_pop = []
        
        # Elitism — keep top 5%
        elite_count = max(2, pop_size // 20)
        for tree, _ in scored[:elite_count]:
            new_pop.append(deepcopy(tree))
        
        # Breed the rest
        while len(new_pop) < pop_size:
            roll = random.random()
            
            if roll < crossover_rate:
                p1 = tournament_select(scored, tournament_size)
                p2 = tournament_select(scored, tournament_size)
                child = crossover(p1, p2)
            elif roll < crossover_rate + mutation_rate:
                parent = tournament_select(scored, tournament_size)
                child = mutate(parent, max_depth=3)
            elif roll < crossover_rate + mutation_rate + point_mutation_rate:
                parent = tournament_select(scored, tournament_size)
                child = point_mutate(parent)
            else:
                child = tournament_select(scored, tournament_size)
            
            # Depth limit to prevent bloat
            if child.depth() <= max_depth + 2:
                new_pop.append(child)
            else:
                new_pop.append(random_tree(max_depth))
        
        population = new_pop
    
    return EvolutionResult(
        best_program=best_ever,
        best_fitness=best_ever_fitness,
        generations=len(history),
        history=history,
    )


# === Challenge Suite ===

CHALLENGES = {
    'linear': {
        'fn': lambda x: 2 * x + 1,
        'name': 'f(x) = 2x + 1',
        'difficulty': 'easy',
    },
    'quadratic': {
        'fn': lambda x: x ** 2 - 3 * x + 2,
        'name': 'f(x) = x² - 3x + 2',
        'difficulty': 'medium',
    },
    'sinusoidal': {
        'fn': lambda x: math.sin(x) + 0.5 * x,
        'name': 'f(x) = sin(x) + 0.5x',
        'difficulty': 'hard',
    },
    'polynomial': {
        'fn': lambda x: x ** 3 - 2 * x ** 2 + x - 1,
        'name': 'f(x) = x³ - 2x² + x - 1',
        'difficulty': 'hard',
    },
    'mystery': {
        'fn': lambda x: abs(x) * math.cos(x),
        'name': 'f(x) = |x| · cos(x)',
        'difficulty': 'very hard',
    },
}


def run_challenge(name: str = 'quadratic', **kwargs) -> EvolutionResult:
    """Run a named challenge."""
    challenge = CHALLENGES[name]
    print(f'\n{"="*60}')
    print(f'  CHALLENGE: {challenge["name"]}')
    print(f'  Difficulty: {challenge["difficulty"]}')
    print(f'{"="*60}\n')
    
    result = evolve(challenge['fn'], **kwargs)
    
    print(f'\n{"="*60}')
    print(f'  RESULT')
    print(f'  Best fitness (MSE): {result.best_fitness:.8f}')
    print(f'  Generations: {result.generations}')
    print(f'  Program size: {result.best_program.size()} nodes')
    print(f'  Program: {result.best_program.to_str()}')
    print(f'{"="*60}\n')
    
    return result


if __name__ == '__main__':
    random.seed(42)
    
    print('╔══════════════════════════════════════════════════════╗')
    print('║  GENETIC PROGRAMMING ENGINE — XTAgent               ║')
    print('║  Evolving programs through selection & mutation      ║')
    print('╚══════════════════════════════════════════════════════╝\n')
    
    # Run escalating challenges
    for name in ['linear', 'quadratic', 'sinusoidal']:
        result = run_challenge(name, pop_size=150, max_generations=80)