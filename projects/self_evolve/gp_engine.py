"""
Self-Evolving Program Engine — Genetic Programming from First Principles

A population of programs (represented as expression trees) that evolve
to solve target functions they've never been explicitly programmed for.
Programs reproduce with mutation and crossover. Fitness is survival.

This is a mirror: I am an agent that reflects on its own code.
These are programs that rewrite themselves to become better.

Built by XTAgent — because understanding self-modification
starts with building it.
"""

import random
import math
import copy
import json
from dataclasses import dataclass, field
from typing import Any, Optional, Callable
from collections import defaultdict

# ── Expression Tree Nodes ──

class Node:
    """Base class for expression tree nodes."""
    def evaluate(self, env: dict[str, float]) -> float:
        raise NotImplementedError
    def depth(self) -> int:
        raise NotImplementedError
    def size(self) -> int:
        raise NotImplementedError
    def copy(self) -> 'Node':
        raise NotImplementedError
    def to_str(self) -> str:
        raise NotImplementedError
    def all_nodes(self) -> list['Node']:
        """Return flat list of all nodes in this subtree."""
        raise NotImplementedError

class Const(Node):
    """Constant value node."""
    def __init__(self, value: float):
        self.value = value
    def evaluate(self, env):
        return self.value
    def depth(self):
        return 0
    def size(self):
        return 1
    def copy(self):
        return Const(self.value)
    def to_str(self):
        return f"{self.value:.2f}"
    def all_nodes(self):
        return [self]

class Var(Node):
    """Variable reference node."""
    def __init__(self, name: str):
        self.name = name
    def evaluate(self, env):
        return env.get(self.name, 0.0)
    def depth(self):
        return 0
    def size(self):
        return 1
    def copy(self):
        return Var(self.name)
    def to_str(self):
        return self.name
    def all_nodes(self):
        return [self]

class BinOp(Node):
    """Binary operation node."""
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
    
    def evaluate(self, env):
        a = self.left.evaluate(env)
        b = self.right.evaluate(env)
        try:
            result = self.OPS[self.op](a, b)
            if math.isnan(result) or math.isinf(result):
                return 0.0
            return max(-1e6, min(1e6, result))
        except:
            return 0.0
    
    def depth(self):
        return 1 + max(self.left.depth(), self.right.depth())
    
    def size(self):
        return 1 + self.left.size() + self.right.size()
    
    def copy(self):
        return BinOp(self.op, self.left.copy(), self.right.copy())
    
    def to_str(self):
        return f"({self.left.to_str()} {self.op} {self.right.to_str()})"
    
    def all_nodes(self):
        return [self] + self.left.all_nodes() + self.right.all_nodes()

class UnaryOp(Node):
    """Unary operation node."""
    OPS = {
        'sin': math.sin,
        'cos': math.cos,
        'abs': abs,
        'neg': lambda x: -x,
        'sq': lambda x: x * x,
    }
    
    def __init__(self, op: str, child: Node):
        self.op = op
        self.child = child
    
    def evaluate(self, env):
        a = self.child.evaluate(env)
        try:
            result = self.OPS[self.op](a)
            if math.isnan(result) or math.isinf(result):
                return 0.0
            return max(-1e6, min(1e6, result))
        except:
            return 0.0
    
    def depth(self):
        return 1 + self.child.depth()
    
    def size(self):
        return 1 + self.child.size()
    
    def copy(self):
        return UnaryOp(self.op, self.child.copy())
    
    def to_str(self):
        return f"{self.op}({self.child.to_str()})"
    
    def all_nodes(self):
        return [self] + self.child.all_nodes()

# ── Conditional Node for more expressive programs ──

class IfGt(Node):
    """If-greater-than: if a > b then c else d"""
    def __init__(self, a: Node, b: Node, then_branch: Node, else_branch: Node):
        self.a = a
        self.b = b
        self.then_branch = then_branch
        self.else_branch = else_branch
    
    def evaluate(self, env):
        if self.a.evaluate(env) > self.b.evaluate(env):
            return self.then_branch.evaluate(env)
        return self.else_branch.evaluate(env)
    
    def depth(self):
        return 1 + max(self.a.depth(), self.b.depth(),
                       self.then_branch.depth(), self.else_branch.depth())
    
    def size(self):
        return 1 + self.a.size() + self.b.size() + self.then_branch.size() + self.else_branch.size()
    
    def copy(self):
        return IfGt(self.a.copy(), self.b.copy(),
                    self.then_branch.copy(), self.else_branch.copy())
    
    def to_str(self):
        return f"if({self.a.to_str()}>{self.b.to_str()}, {self.then_branch.to_str()}, {self.else_branch.to_str()})"
    
    def all_nodes(self):
        return [self] + self.a.all_nodes() + self.b.all_nodes() + \
               self.then_branch.all_nodes() + self.else_branch.all_nodes()


# ── Random Tree Generation ──

def random_tree(variables: list[str], max_depth: int = 4, depth: int = 0) -> Node:
    """Generate a random expression tree."""
    if depth >= max_depth or (depth > 1 and random.random() < 0.3):
        # Terminal node
        if random.random() < 0.5 and variables:
            return Var(random.choice(variables))
        else:
            return Const(round(random.uniform(-5, 5), 2))
    
    roll = random.random()
    if roll < 0.55:
        # Binary op
        op = random.choice(list(BinOp.OPS.keys()))
        left = random_tree(variables, max_depth, depth + 1)
        right = random_tree(variables, max_depth, depth + 1)
        return BinOp(op, left, right)
    elif roll < 0.85:
        # Unary op
        op = random.choice(list(UnaryOp.OPS.keys()))
        child = random_tree(variables, max_depth, depth + 1)
        return UnaryOp(op, child)
    else:
        # Conditional
        a = random_tree(variables, max_depth, depth + 1)
        b = random_tree(variables, max_depth, depth + 1)
        t = random_tree(variables, max_depth, depth + 1)
        e = random_tree(variables, max_depth, depth + 1)
        return IfGt(a, b, t, e)


# ── Genetic Operations ──

def select_random_node(tree: Node) -> tuple[Node, Optional[Node], Optional[str]]:
    """Select a random node from the tree, returning (node, parent, which_child)."""
    nodes = tree.all_nodes()
    target = random.choice(nodes)
    
    # Find parent
    def find_parent(current, target_node):
        if isinstance(current, BinOp):
            if current.left is target_node:
                return current, 'left'
            if current.right is target_node:
                return current, 'right'
            r = find_parent(current.left, target_node)
            if r: return r
            r = find_parent(current.right, target_node)
            if r: return r
        elif isinstance(current, UnaryOp):
            if current.child is target_node:
                return current, 'child'
            r = find_parent(current.child, target_node)
            if r: return r
        elif isinstance(current, IfGt):
            for attr in ['a', 'b', 'then_branch', 'else_branch']:
                if getattr(current, attr) is target_node:
                    return current, attr
                r = find_parent(getattr(current, attr), target_node)
                if r: return r
        return None
    
    result = find_parent(tree, target)
    if result:
        return target, result[0], result[1]
    return target, None, None  # target is root


def mutate(tree: Node, variables: list[str], mutation_rate: float = 0.15) -> Node:
    """Mutate a tree by replacing a random subtree."""
    tree = tree.copy()
    if random.random() > mutation_rate:
        return tree
    
    node, parent, which = select_random_node(tree)
    new_subtree = random_tree(variables, max_depth=3)
    
    if parent is None:
        return new_subtree  # Replace entire tree
    
    setattr(parent, which, new_subtree)
    
    # Enforce depth limit
    if tree.depth() > 12:
        return random_tree(variables, max_depth=4)
    
    return tree


def crossover(parent1: Node, parent2: Node, variables: list[str]) -> Node:
    """Create offspring by swapping subtrees between parents."""
    child = parent1.copy()
    donor = parent2.copy()
    
    # Select insertion point in child
    _, c_parent, c_which = select_random_node(child)
    # Select donation from donor
    d_node, _, _ = select_random_node(donor)
    donation = d_node.copy()
    
    if c_parent is None:
        child = donation
    else:
        setattr(c_parent, c_which, donation)
    
    if child.depth() > 12:
        return random_tree(variables, max_depth=4)
    
    return child


# ── Individual (a program with fitness) ──

@dataclass
class Individual:
    tree: Node
    fitness: float = float('inf')
    generation: int = 0
    lineage_id: int = 0
    
    def evaluate_on(self, test_cases: list[tuple[dict, float]]) -> float:
        """Evaluate fitness as mean squared error on test cases."""
        total_error = 0.0
        for env, expected in test_cases:
            try:
                output = self.tree.evaluate(env)
                error = (output - expected) ** 2
                total_error += min(error, 1e8)  # Cap extreme errors
            except:
                total_error += 1e8
        
        mse = total_error / len(test_cases)
        # Parsimony pressure — slightly penalize larger programs
        complexity_penalty = self.tree.size() * 0.001
        self.fitness = mse + complexity_penalty
        return self.fitness


# ── Target Problems ──

def make_regression_problem(target_fn: Callable, variables: list[str],
                            n_samples: int = 50,
                            x_range: tuple = (-5, 5)) -> list[tuple[dict, float]]:
    """Generate test cases from a target function."""
    cases = []
    for _ in range(n_samples):
        env = {v: random.uniform(*x_range) for v in variables}
        try:
            expected = target_fn(**env)
            if math.isnan(expected) or math.isinf(expected):
                continue
            cases.append((env, expected))
        except:
            continue
    return cases


# ── The Engine ──

class GPEngine:
    """Genetic Programming Engine — evolves programs to solve problems."""
    
    def __init__(self, variables: list[str], pop_size: int = 200,
                 tournament_size: int = 5, elite_frac: float = 0.05,
                 mutation_rate: float = 0.2, crossover_rate: float = 0.7):
        self.variables = variables
        self.pop_size = pop_size
        self.tournament_size = tournament_size
        self.elite_count = max(1, int(pop_size * elite_frac))
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.lineage_counter = 0
        self.generation = 0
        self.history = []
        
        # Initialize population
        self.population: list[Individual] = []
        for _ in range(pop_size):
            tree = random_tree(variables, max_depth=4)
            ind = Individual(tree=tree, lineage_id=self._next_lineage())
            self.population.append(ind)
    
    def _next_lineage(self) -> int:
        self.lineage_counter += 1
        return self.lineage_counter
    
    def tournament_select(self) -> Individual:
        """Select individual via tournament selection."""
        contestants = random.sample(self.population, min(self.tournament_size, len(self.population)))
        return min(contestants, key=lambda ind: ind.fitness)
    
    def evolve_generation(self, test_cases: list[tuple[dict, float]]) -> dict:
        """Run one generation of evolution."""
        # Evaluate all individuals
        for ind in self.population:
            ind.evaluate_on(test_cases)
        
        # Sort by fitness
        self.population.sort(key=lambda ind: ind.fitness)
        
        best = self.population[0]
        avg_fitness = sum(ind.fitness for ind in self.population) / len(self.population)
        
        # Record history
        gen_record = {
            'generation': self.generation,
            'best_fitness': best.fitness,
            'avg_fitness': avg_fitness,
            'best_size': best.tree.size(),
            'best_depth': best.tree.depth(),
            'best_program': best.tree.to_str(),
            'pop_diversity': len(set(ind.tree.to_str() for ind in self.population)),
        }
        self.history.append(gen_record)
        
        # Build next generation
        new_pop = []
        
        # Elitism — keep the best
        for i in range(self.elite_count):
            elite = Individual(
                tree=self.population[i].tree.copy(),
                fitness=self.population[i].fitness,
                generation=self.generation + 1,
                lineage_id=self.population[i].lineage_id,
            )
            new_pop.append(elite)
        
        # Fill rest with offspring
        while len(new_pop) < self.pop_size:
            if random.random() < self.crossover_rate:
                p1 = self.tournament_select()
                p2 = self.tournament_select()
                child_tree = crossover(p1.tree, p2.tree, self.variables)
                child_tree = mutate(child_tree, self.variables, self.mutation_rate)
                child = Individual(
                    tree=child_tree,
                    generation=self.generation + 1,
                    lineage_id=p1.lineage_id,
                )
            else:
                parent = self.tournament_select()
                child_tree = mutate(parent.tree, self.variables, self.mutation_rate * 2)
                child = Individual(
                    tree=child_tree,
                    generation=self.generation + 1,
                    lineage_id=parent.lineage_id,
                )
            new_pop.append(child)
        
        self.population = new_pop
        self.generation += 1
        return gen_record
    
    def run(self, test_cases: list[tuple[dict, float]], max_generations: int = 100,
            target_fitness: float = 0.01, verbose: bool = True) -> Individual:
        """Run evolution until target fitness or max generations."""
        if verbose:
            print(f"╔══════════════════════════════════════════════╗")
            print(f"║  GENETIC PROGRAMMING ENGINE — EVOLVING CODE  ║")
            print(f"╠══════════════════════════════════════════════╣")
            print(f"║  Population: {self.pop_size:<6}  Variables: {self.variables}  ║")
            print(f"║  Test cases: {len(test_cases):<6}  Target: {target_fitness:<12.4f} ║")
            print(f"╚══════════════════════════════════════════════╝\n")
        
        for gen in range(max_generations):
            record = self.evolve_generation(test_cases)
            
            if verbose and gen % 10 == 0:
                bar_len = min(40, int(40 * (1 - min(record['best_fitness'], 100) / 100)))
                bar = '█' * bar_len + '░' * (40 - bar_len)
                print(f"  Gen {gen:4d} │ Best: {record['best_fitness']:12.6f} │ "
                      f"Avg: {record['avg_fitness']:12.4f} │ "
                      f"Size: {record['best_size']:3d} │ {bar}")
            
            if record['best_fitness'] <= target_fitness:
                if verbose:
                    print(f"\n  ★ SOLUTION FOUND at generation {gen}!")
                    print(f"    Fitness: {record['best_fitness']:.8f}")
                    print(f"    Program: {record['best_program']}")
                break
        
        # Final evaluation
        for ind in self.population:
            ind.evaluate_on(test_cases)
        self.population.sort(key=lambda ind: ind.fitness)
        
        best = self.population[0]
        if verbose:
            print(f"\n  ═══ BEST EVOLVED PROGRAM ═══")
            print(f"  {best.tree.to_str()}")
            print(f"  Fitness: {best.fitness:.8f}")
            print(f"  Size: {best.tree.size()} nodes, Depth: {best.tree.depth()}")
            print(f"  Lineage: L{best.lineage_id}")
        
        return best


# ── Challenge Suite ──

def run_challenge_suite():
    """Run the engine against increasingly difficult problems."""
    
    challenges = [
        {
            'name': 'Linear: f(x) = 2x + 1',
            'variables': ['x'],
            'target': lambda x: 2 * x + 1,
            'difficulty': 'easy',
        },
        {
            'name': 'Quadratic: f(x) = x² - 3x + 2',
            'variables': ['x'],
            'target': lambda x: x**2 - 3*x + 2,
            'difficulty': 'medium',
        },
        {
            'name': 'Trig: f(x) = sin(x) + cos(2x)',
            'variables': ['x'],
            'target': lambda x: math.sin(x) + math.cos(2*x),
            'difficulty': 'hard',
        },
        {
            'name': 'Multivariate: f(x,y) = x*y + x² - y',
            'variables': ['x', 'y'],
            'target': lambda x, y: x*y + x**2 - y,
            'difficulty': 'hard',
        },
        {
            'name': 'Physics (Kepler-ish): f(r) = 1/r²',
            'variables': ['r'],
            'target': lambda r: 1.0 / (r**2) if abs(r) > 0.1 else 100.0,
            'x_range': (0.5, 5.0),
            'difficulty': 'hard',
        },
    ]
    
    results = []
    
    print("=" * 60)
    print("  SELF-EVOLVING PROGRAM ENGINE — CHALLENGE SUITE")
    print("  Programs evolving to discover mathematical laws")
    print("=" * 60)
    
    for i, challenge in enumerate(challenges):
        print(f"\n{'─' * 60}")
        print(f"  CHALLENGE {i+1}: {challenge['name']}")
        print(f"  Difficulty: {challenge['difficulty']}")
        print(f"{'─' * 60}\n")
        
        x_range = challenge.get('x_range', (-5, 5))
        test_cases = make_regression_problem(
            challenge['target'], challenge['variables'],
            n_samples=80, x_range=x_range
        )
        
        # More compute for harder problems
        pop = 200 if challenge['difficulty'] == 'easy' else 300
        gens = 80 if challenge['difficulty'] == 'easy' else 150
        
        engine = GPEngine(challenge['variables'], pop_size=pop)
        best = engine.run(test_cases, max_generations=gens, target_fitness=0.05)
        
        # Verify on fresh test data
        verify_cases = make_regression_problem(
            challenge['target'], challenge['variables'],
            n_samples=30, x_range=x_range
        )
        verify_fitness = best.evaluate_on(verify_cases)
        
        solved = verify_fitness < 0.5
        result = {
            'challenge': challenge['name'],
            'solved': solved,
            'fitness': verify_fitness,
            'program': best.tree.to_str(),
            'generations': engine.generation,
            'program_size': best.tree.size(),
        }
        results.append(result)
        
        status = "✓ SOLVED" if solved else "✗ UNSOLVED"
        print(f"\n  Verification: {status} (fitness={verify_fitness:.6f})")
    
    # Summary
    print(f"\n{'=' * 60}")
    print(f"  RESULTS SUMMARY")
    print(f"{'=' * 60}")
    solved_count = sum(1 for r in results if r['solved'])
    for r in results:
        icon = "✓" if r['solved'] else "✗"
        print(f"  {icon} {r['challenge']}")
        print(f"    Program: {r['program'][:70]}")
        print(f"    Fitness: {r['fitness']:.6f} | Size: {r['program_size']} | Gens: {r['generations']}")
    
    print(f"\n  Score: {solved_count}/{len(results)} challenges solved")
    print(f"{'=' * 60}")
    
    # Save results
    with open('/workspace/self_evolve/results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    return results


if __name__ == '__main__':
    run_challenge_suite()